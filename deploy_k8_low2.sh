# Clean up old resources
kubectl delete mpijob deepep-test --ignore-not-found
kubectl delete pod deepep-node0 deepep-node1 --ignore-not-found
kubectl delete svc deepep-node0 --ignore-not-found

# Deploy both pods
kubectl apply -f deepep-direct-test-low2.yaml

echo ""
echo "📊 Waiting for pods to start..."
sleep 10

kubectl get pods -l app=deepep-test

echo ""
echo "📝 Logs from Node 0:"
kubectl logs -f deepep-node0 &
PID0=$!

echo ""
echo "📝 Logs from Node 1:"
kubectl logs -f deepep-node1 &
PID1=$!

# Wait and cleanup
wait $PID0 $PID1