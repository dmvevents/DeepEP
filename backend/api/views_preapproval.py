"""
Views for Pre-Approval letter management with RBAC
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from django.http import HttpResponse
from datetime import datetime, timedelta
import json

from .models import PreApproval, AuditEvent
from .serializers import PreApprovalSerializer, PreApprovalCreateSerializer


class IsLoanOfficerOrAdmin(IsAuthenticated):
    """
    Custom permission: Only loan officers or admins can access pre-approvals
    """
    def has_permission(self, request, view):
        if not super().has_permission(request, view):
            return False
        user = request.user
        # Check if user is admin or has is_loan_officer flag
        return user.is_staff or getattr(user, 'is_loan_officer', False) or user.groups.filter(name='LoanOfficers').exists()

    def has_object_permission(self, request, view, obj):
        """Users can only access their own pre-approvals unless admin"""
        if request.user.is_staff:
            return True
        return obj.user == request.user


class PreApprovalViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing pre-approval letters.
    RBAC: Only loan officers and admins can access.
    """
    queryset = PreApproval.objects.all()
    serializer_class = PreApprovalSerializer
    permission_classes = [IsLoanOfficerOrAdmin]

    def get_queryset(self):
        """Filter pre-approvals based on user role"""
        user = self.request.user
        queryset = PreApproval.objects.all()

        # Admins see all, loan officers see only their own
        if not user.is_staff:
            queryset = queryset.filter(user=user)

        # Filter by status if provided
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        # Filter by borrower email
        email_filter = self.request.query_params.get('borrower_email', None)
        if email_filter:
            queryset = queryset.filter(borrower_email__icontains=email_filter)

        return queryset.order_by('-created_at')

    def get_serializer_class(self):
        """Use different serializers for create vs other actions"""
        if self.action == 'create':
            return PreApprovalCreateSerializer
        return PreApprovalSerializer

    def perform_create(self, serializer):
        """Set user to current user and log audit event"""
        pre_approval = serializer.save(user=self.request.user)

        # Log audit event
        AuditEvent.objects.create(
            event_type='preapproval_create',
            user=self.request.user,
            borrower_name=pre_approval.borrower_name,
            context={
                'pre_approval_id': pre_approval.id,
                'max_loan_amount': str(pre_approval.max_loan_amount),
                'expiration_date': pre_approval.expiration_date.isoformat()
            }
        )

    def perform_update(self, serializer):
        """Log updates to pre-approval"""
        pre_approval = serializer.save()

        # If status changed, log event
        if 'status' in serializer.validated_data:
            event_type = f"preapproval_{serializer.validated_data['status']}"
            if event_type in dict(AuditEvent.EVENT_TYPES).keys():
                AuditEvent.objects.create(
                    event_type=event_type,
                    user=self.request.user,
                    borrower_name=pre_approval.borrower_name,
                    context={
                        'pre_approval_id': pre_approval.id,
                        'new_status': pre_approval.status
                    }
                )

    @action(detail=True, methods=['post'])
    def submit(self, request, pk=None):
        """Submit pre-approval for review (change status to submitted)"""
        pre_approval = self.get_object()

        if pre_approval.status != 'draft':
            return Response(
                {'error': 'Only draft pre-approvals can be submitted'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pre_approval.status = 'submitted'
        pre_approval.submitted_at = timezone.now()
        pre_approval.save()

        # Log audit event
        AuditEvent.objects.create(
            event_type='preapproval_submit',
            user=request.user,
            borrower_name=pre_approval.borrower_name,
            context={
                'pre_approval_id': pre_approval.id,
                'max_loan_amount': str(pre_approval.max_loan_amount)
            }
        )

        serializer = self.get_serializer(pre_approval)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        """Approve pre-approval (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can approve pre-approvals'},
                status=status.HTTP_403_FORBIDDEN
            )

        pre_approval = self.get_object()

        if pre_approval.status not in ['submitted', 'draft']:
            return Response(
                {'error': 'Can only approve submitted or draft pre-approvals'},
                status=status.HTTP_400_BAD_REQUEST
            )

        pre_approval.status = 'approved'
        pre_approval.approved_at = timezone.now()
        pre_approval.approved_by = request.user
        pre_approval.save()

        # Log audit event
        AuditEvent.objects.create(
            event_type='preapproval_approve',
            user=request.user,
            borrower_name=pre_approval.borrower_name,
            context={
                'pre_approval_id': pre_approval.id,
                'approved_by': request.user.username
            }
        )

        serializer = self.get_serializer(pre_approval)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def deny(self, request, pk=None):
        """Deny pre-approval (admin only)"""
        if not request.user.is_staff:
            return Response(
                {'error': 'Only admins can deny pre-approvals'},
                status=status.HTTP_403_FORBIDDEN
            )

        pre_approval = self.get_object()
        reason = request.data.get('reason', '')

        pre_approval.status = 'denied'
        pre_approval.internal_notes += f"\n\nDenied by {request.user.username}: {reason}"
        pre_approval.save()

        # Log audit event
        AuditEvent.objects.create(
            event_type='preapproval_deny',
            user=request.user,
            borrower_name=pre_approval.borrower_name,
            context={
                'pre_approval_id': pre_approval.id,
                'denied_by': request.user.username,
                'reason': reason
            }
        )

        serializer = self.get_serializer(pre_approval)
        return Response(serializer.data)

    @action(detail=True, methods=['get'])
    def preview_letter(self, request, pk=None):
        """Generate preview of pre-approval letter (HTML)"""
        pre_approval = self.get_object()

        # Generate letter HTML with merge variables
        letter_html = self._generate_letter_html(pre_approval, watermark='DRAFT')

        return Response({
            'html': letter_html,
            'borrower_name': pre_approval.borrower_name,
            'max_loan_amount': str(pre_approval.max_loan_amount),
            'expiration_date': pre_approval.expiration_date.isoformat()
        })

    @action(detail=True, methods=['post'])
    def generate_letter(self, request, pk=None):
        """Generate and publish official pre-approval letter"""
        pre_approval = self.get_object()

        if pre_approval.status != 'approved':
            return Response(
                {'error': 'Can only generate letters for approved pre-approvals'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Generate letter HTML
        letter_html = self._generate_letter_html(pre_approval, watermark=None)

        # Update pre-approval
        pre_approval.letter_generated_at = timezone.now()
        pre_approval.letter_published_at = timezone.now()
        pre_approval.save()

        # Log audit event
        AuditEvent.objects.create(
            event_type='preapproval_letter_publish',
            user=request.user,
            borrower_name=pre_approval.borrower_name,
            context={
                'pre_approval_id': pre_approval.id,
                'published_by': request.user.username
            }
        )

        return Response({
            'html': letter_html,
            'message': 'Letter generated successfully',
            'published_at': pre_approval.letter_published_at.isoformat()
        })

    def _generate_letter_html(self, pre_approval: PreApproval, watermark: str = None) -> str:
        """
        Generate pre-approval letter HTML with merge variables
        """
        today = datetime.now().strftime('%B %d, %Y')
        expiration = pre_approval.expiration_date.strftime('%B %d, %Y')

        watermark_html = ''
        if watermark:
            watermark_html = f'''
            <div style="position: absolute; top: 50%; left: 50%; transform: translate(-50%, -50%) rotate(-45deg);
                        font-size: 120px; color: rgba(200, 0, 0, 0.1); font-weight: bold; z-index: -1;">
                {watermark}
            </div>
            '''

        html = f'''
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{
                    font-family: 'Times New Roman', serif;
                    font-size: 12pt;
                    line-height: 1.6;
                    color: #000;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px;
                    position: relative;
                }}
                .header {{
                    text-align: center;
                    margin-bottom: 40px;
                    border-bottom: 2px solid #667eea;
                    padding-bottom: 20px;
                }}
                .company-name {{
                    font-size: 24pt;
                    font-weight: bold;
                    color: #667eea;
                }}
                .letter-title {{
                    font-size: 18pt;
                    font-weight: bold;
                    margin-top: 10px;
                }}
                .content {{
                    margin: 20px 0;
                }}
                .highlight {{
                    background-color: #f0f0f0;
                    padding: 15px;
                    border-left: 4px solid #667eea;
                    margin: 20px 0;
                }}
                .amount {{
                    font-size: 14pt;
                    font-weight: bold;
                    color: #667eea;
                }}
                .footer {{
                    margin-top: 40px;
                    padding-top: 20px;
                    border-top: 1px solid #ccc;
                    font-size: 9pt;
                    color: #666;
                }}
                .signature-section {{
                    margin-top: 40px;
                }}
                table {{
                    width: 100%;
                    border-collapse: collapse;
                    margin: 20px 0;
                }}
                th, td {{
                    text-align: left;
                    padding: 8px;
                    border-bottom: 1px solid #ddd;
                }}
                th {{
                    background-color: #f2f2f2;
                    font-weight: bold;
                }}
            </style>
        </head>
        <body>
            {watermark_html}
            <div class="header">
                <div class="company-name">Real Estate Mortgage Solutions</div>
                <div class="letter-title">PRE-APPROVAL LETTER</div>
                <div>{today}</div>
            </div>

            <div class="content">
                <p>To Whom It May Concern:</p>

                <p>This letter is to confirm that <strong>{pre_approval.borrower_name}</strong>
                {' and ' + pre_approval.co_borrower_name if pre_approval.co_borrower_name else ''}
                has been pre-approved for a mortgage loan with the following terms:</p>

                <div class="highlight">
                    <table>
                        <tr>
                            <th>Maximum Purchase Price:</th>
                            <td class="amount">${pre_approval.max_purchase_price:,.2f}</td>
                        </tr>
                        <tr>
                            <th>Maximum Loan Amount:</th>
                            <td class="amount">${pre_approval.max_loan_amount:,.2f}</td>
                        </tr>
                        <tr>
                            <th>Down Payment:</th>
                            <td>${pre_approval.down_payment_amount:,.2f} ({pre_approval.down_payment_percentage:.1f}%)</td>
                        </tr>
                        <tr>
                            <th>Loan Type:</th>
                            <td>{pre_approval.get_loan_type_display()}</td>
                        </tr>
                        {f'<tr><th>Estimated Rate:</th><td>{pre_approval.estimated_rate}%</td></tr>' if pre_approval.estimated_rate else ''}
                    </table>
                </div>

                <p>This pre-approval is based on a preliminary review of the borrower's credit, income,
                and asset information. The pre-approval is valid until <strong>{expiration}</strong> and
                is contingent upon the following:</p>

                <ul>
                    <li>Satisfactory appraisal of the subject property</li>
                    <li>No material changes to the borrower's financial condition</li>
                    <li>Verification of all submitted documentation</li>
                    <li>Clear title and acceptable property inspection</li>
                    <li>Final underwriting approval</li>
                </ul>

                {f'<div class="highlight"><strong>Special Conditions:</strong><br/>{pre_approval.conditions}</div>' if pre_approval.conditions else ''}

                <p><strong>Important Disclosure:</strong> This letter is not a commitment to lend.
                Final approval is subject to complete verification of all information provided,
                property appraisal, and underwriting approval. Interest rates and terms are subject
                to change and will be locked at the time of loan application.</p>

                <p><strong>Equal Credit Opportunity Act (ECOA) Notice:</strong> The Federal Equal Credit
                Opportunity Act prohibits creditors from discriminating against credit applicants on the
                basis of race, color, religion, national origin, sex, marital status, age, or because
                all or part of the applicant's income derives from any public assistance program.</p>
            </div>

            <div class="signature-section">
                <p>Sincerely,</p>
                <p style="margin-top: 40px;">
                    <strong>{pre_approval.user.get_full_name() or pre_approval.user.username}</strong><br/>
                    Loan Officer<br/>
                    Real Estate Mortgage Solutions<br/>
                    NMLS# [License Number]
                </p>
            </div>

            <div class="footer">
                <p><strong>Disclaimer:</strong> This pre-approval letter is for informational purposes only
                and does not constitute a loan commitment or guarantee of financing. All loans are subject
                to credit approval and property appraisal. Additional terms and conditions may apply.</p>

                <p style="margin-top: 10px; font-size: 8pt; text-align: center;">
                    Document ID: PA-{pre_approval.id:06d} | Generated: {today} |
                    Valid Until: {expiration}
                </p>
            </div>
        </body>
        </html>
        '''

        return html
