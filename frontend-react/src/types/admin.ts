// Admin Role & Permission Types

export type UserRole = 'super_admin' | 'admin' | 'user';

export interface AdminProfile {
  id: string;
  user_id: string;
  email: string;
  first_name: string;
  last_name: string;
  role: UserRole;
  phone: string;
  license_number?: string;
  nmls_id?: string; // National Mortgage Licensing System ID
  territory: string[]; // States/counties they cover
  profile_photo?: string;
  bio?: string;
  is_active: boolean;
  two_factor_enabled: boolean;
  created_at: string;
  updated_at: string;
  last_login?: string;
  created_by?: string; // Super admin who created this account

  // Statistics
  applications_reviewed?: number;
  avg_review_time_hours?: number;
  approval_rate?: number;
}

export interface Permission {
  resource: string;
  actions: ('create' | 'read' | 'update' | 'delete')[];
}

export interface RolePermissions {
  role: UserRole;
  permissions: Permission[];
}

// Permission Matrix
export const ROLE_PERMISSIONS: RolePermissions[] = [
  {
    role: 'super_admin',
    permissions: [
      { resource: 'admins', actions: ['create', 'read', 'update', 'delete'] },
      { resource: 'applications', actions: ['create', 'read', 'update', 'delete'] },
      { resource: 'users', actions: ['create', 'read', 'update', 'delete'] },
      { resource: 'documents', actions: ['read', 'delete'] },
      { resource: 'audit_logs', actions: ['read'] },
      { resource: 'system_settings', actions: ['read', 'update'] },
    ],
  },
  {
    role: 'admin',
    permissions: [
      { resource: 'applications', actions: ['read', 'update'] },
      { resource: 'users', actions: ['read'] },
      { resource: 'documents', actions: ['read'] },
      { resource: 'own_profile', actions: ['read', 'update'] },
    ],
  },
  {
    role: 'user',
    permissions: [
      { resource: 'own_applications', actions: ['create', 'read', 'update', 'delete'] },
      { resource: 'own_documents', actions: ['create', 'read', 'delete'] },
      { resource: 'own_profile', actions: ['read', 'update'] },
    ],
  },
];

export interface AuditLog {
  id: string;
  admin_id: string;
  admin_name: string;
  action: string; // 'viewed_application', 'updated_status', 'viewed_document', etc.
  resource_type: string; // 'application', 'user', 'document'
  resource_id: string;
  details: string;
  ip_address: string;
  timestamp: string;
  sensitive_data_accessed: boolean; // Flag for PII/financial data access
}

export interface SessionInfo {
  user_id: string;
  role: UserRole;
  session_id: string;
  expires_at: string;
  last_activity: string;
  ip_address: string;
}

// Helper function to check permissions
export const hasPermission = (
  userRole: UserRole,
  resource: string,
  action: 'create' | 'read' | 'update' | 'delete'
): boolean => {
  const rolePermissions = ROLE_PERMISSIONS.find(rp => rp.role === userRole);
  if (!rolePermissions) return false;

  const resourcePermission = rolePermissions.permissions.find(p => p.resource === resource);
  if (!resourcePermission) return false;

  return resourcePermission.actions.includes(action);
};

// Helper to check if user is admin or higher
export const isAdminOrHigher = (role: UserRole): boolean => {
  return role === 'admin' || role === 'super_admin';
};

// Helper to check if user is super admin
export const isSuperAdmin = (role: UserRole): boolean => {
  return role === 'super_admin';
};
