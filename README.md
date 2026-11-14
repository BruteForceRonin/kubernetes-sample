# Kubernetes practice with Python

Use the supplied Python app and Dockerfile to build an image, then write the Kubernetes manifests that run two copies of the app. The HTTP response shows the app version and the hostname of the instance that answered.

```text
app.py                 Runnable Python HTTP demo
Dockerfile             Ready-to-build container image definition
k8s/
  deployment.yaml      Replica and container exercise
  service.yaml         Networking exercise
```

Run commands in PowerShell from this folder. For the cluster labs, start Docker Desktop in Linux container mode and use its `kubeadm` Kubernetes cluster, as in the reference lab. Confirm that Docker reports `linux` and the Kubernetes node is `Ready`. [Docker Desktop Kubernetes setup](https://docs.docker.com/desktop/use-desktop/kubernetes/)

```powershell
docker info --format '{{.OSType}}'
kubectl --context docker-desktop get nodes
```

## Optional check — Run Python locally

```powershell
python app.py
```

From a second terminal, call both routes. Expect `version: v1` and your machine's hostname from the first request and an `ok` status from the second. Check the server terminal for request logs. Stop Python with Ctrl+C before continuing.

```powershell
Invoke-RestMethod http://127.0.0.1:8000/
Invoke-RestMethod http://127.0.0.1:8000/healthz
```

## 1. Build the supplied image

Build the image locally so the Kubernetes node can use it. The Dockerfile configures the app to listen on port 8000 inside the container.

```powershell
docker build -t python-k8s-demo:v1 .
```

To smoke-test the image before deploying it, run this command, then call `Invoke-RestMethod http://127.0.0.1:8080/` in a second terminal. Stop the container with Ctrl+C before port-forwarding.

```powershell
docker run --rm -p 127.0.0.1:8080:8000 python-k8s-demo:v1
```

## 2. Deploy and connect

Write the two manifests using their prompts. The Deployment selector must match the Pod template's labels. The Service uses its own selector to find those same Pods. Predict which port the browser, Service, and Python process each use.

```powershell
kubectl --context docker-desktop apply -f k8s/
kubectl --context docker-desktop rollout status deployment/python-demo --timeout=90s
kubectl --context docker-desktop get rs,pods -l app=python-demo
kubectl --context docker-desktop get deployment,svc python-demo
kubectl --context docker-desktop port-forward service/python-demo 8080:80
```

Use `app: python-demo` on the Pod template. Call `http://127.0.0.1:8080/` in a browser or a second terminal. Service port-forwarding selects one Pod for the session. Start a fresh session if that Pod terminates. [kubectl port-forward](https://kubernetes.io/docs/reference/kubectl/generated/kubectl_port-forward/)

## 3. Scale, replace, and inspect Pods

Stop port-forwarding with Ctrl+C. Watch the Pods in one terminal and, from a second terminal, scale from two to five and back to two. Wait for the count to settle at each step.

```powershell
kubectl --context docker-desktop get pods -l app=python-demo -w
```

```powershell
kubectl --context docker-desktop scale deployment/python-demo --replicas=5
# Once all five Pods are running:
kubectl --context docker-desktop scale deployment/python-demo --replicas=2
```

Pick a running Pod from the watch output and replace `YOUR_POD_NAME` below. Check whether the replacement has the same name. Forward the Service again and make an HTTP request before checking the logs.

```powershell
kubectl --context docker-desktop delete pod YOUR_POD_NAME
kubectl --context docker-desktop logs -l app=python-demo --prefix=true --tail=20
kubectl --context docker-desktop describe deployment python-demo
kubectl --context docker-desktop describe service python-demo
kubectl --context docker-desktop describe pod YOUR_REPLACEMENT_NAME
kubectl --context docker-desktop exec YOUR_REPLACEMENT_NAME -- hostname
```

## 4. Update and roll back

Change `VERSION` in `app.py` to `v2`. Build a second image tag, leaving the first image available for rollback. Change the Deployment's image tag to `v2`, then apply the manifest.

```powershell
docker build -t python-k8s-demo:v2 .
kubectl --context docker-desktop apply -f k8s/deployment.yaml
kubectl --context docker-desktop rollout status deployment/python-demo --timeout=90s
kubectl --context docker-desktop rollout history deployment/python-demo
```

Start a fresh port-forward and confirm the response says `v2`. Stop forwarding, roll back, then start another port-forward and check for `v1`.

```powershell
kubectl --context docker-desktop rollout undo deployment/python-demo
kubectl --context docker-desktop rollout status deployment/python-demo --timeout=90s
```

Predict which version a fresh `kubectl apply -f k8s/deployment.yaml` would select while the file still says `v2`. [Deployment rollback](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/#rolling-back-a-deployment)

## 5. Clean up

Stop port-forwarding and any Pod watch with Ctrl+C. Delete the resources from this lab. To rerun from v1 later, restore the version in `app.py` and the image tag in the Deployment.

```powershell
kubectl --context docker-desktop delete -f k8s/
kubectl --context docker-desktop get pods -l app=python-demo
docker image rm python-k8s-demo:v1 python-k8s-demo:v2
```

If a Pod fails to start, inspect its Events with `kubectl describe pod`. With `imagePullPolicy: Never`, `ErrImageNeverPull` means the node could not find the exact image locally. Compare the manifest tag and `docker image ls`, then verify that the cluster can see the same image store. If the Service has no endpoints, compare its selector with `kubectl --context docker-desktop get pods --show-labels`.
