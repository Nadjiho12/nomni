# Virtualization, containers, and isolation for AI and engineering work

*Last updated: 2026-10-13 | Version-sensitive: Docker/Kubernetes/NVIDIA toolkit versions; cloud GPU offerings | Re-check current docs before pinning versions, prices, or API names.*

Choose the right isolation layer for the job: reproducible dev environments, GPU workloads, untrusted code execution, malware-safe analysis labs, and scalable deployment. Commands here were not run in the sandbox (no hypervisor or container runtime available); verify on your machine.

## Contents
1. The isolation spectrum
2. Containers (Docker/Podman)
3. Virtual machines (KVM, VirtualBox, VMware, Proxmox, Hyper-V)
4. GPU access and virtualization
5. Kubernetes basics for AI workloads
6. Sandboxing untrusted code and AI tools
7. Lab design (security and AI)
8. Reproducible environments
9. Networking and storage
10. Cost and operations
11. Verification

## 1. The isolation spectrum

| Layer | Isolation | Overhead | Use for |
|---|---|---|---|
| Virtual environment (venv, conda, nvm) | Dependencies only | None | Python/Node project deps |
| Container (Docker/Podman) | Process, filesystem, network namespaces; shared kernel | Low | Reproducible apps, services, CI, most AI serving |
| Hardened container (gVisor, Kata, rootless, seccomp) | Stronger syscall/kernel barrier | Low-medium | Running semi-trusted code |
| MicroVM (Firecracker, Cloud Hypervisor) | Separate kernel, fast boot | Medium | Multi-tenant code execution, serverless |
| Full VM (KVM/QEMU, VMware, Hyper-V, VirtualBox) | Separate kernel and virtual hardware | Medium-high | Different OS, strong isolation, malware analysis, lab networks |
| Bare metal / dedicated host | Physical | Highest cost | Maximum performance or compliance |
Pick the **weakest isolation that meets the threat model**; use VMs for untrusted or hostile code, containers for your own services.

## 2. Containers (Docker/Podman)

```dockerfile
# Python ML service, small, non-root, reproducible
FROM python:3.11-slim AS base
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY src/ src/
RUN useradd -m app && chown -R app /app
USER app
EXPOSE 8000
HEALTHCHECK CMD python -c "import urllib.request;urllib.request.urlopen('http://localhost:8000/health')" || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```
```bash
docker build -t svc:1.0 . && docker run --rm -p 8000:8000 --read-only --tmpfs /tmp \
  --cap-drop ALL --security-opt no-new-privileges --memory 2g --cpus 2 svc:1.0
docker compose up -d --build        # multi-service dev stack
```
Practices: pin base image versions (digest for production), multi-stage builds, `.dockerignore`, no secrets in images (use env/secret mounts), scan images (`trivy image svc:1.0`), run as non-root, read-only filesystem, drop capabilities, set CPU/memory limits, health checks, one process per container, logs to stdout. Rootless Podman is a good default on shared machines.

## 3. Virtual machines (KVM, VirtualBox, VMware, Proxmox, Hyper-V)

- **Linux KVM/QEMU with libvirt:** best performance on Linux. Check CPU support (`egrep -c '(vmx|svm)' /proc/cpuinfo`), install `qemu-kvm libvirt-daemon-system virt-manager`, manage with `virsh`.
```bash
virt-install --name lab-ubuntu --memory 4096 --vcpus 2 --disk size=40 \
  --cdrom ubuntu-24.04.iso --os-variant ubuntu24.04 --network network=default
virsh list --all; virsh snapshot-create-as lab-ubuntu clean-install; virsh snapshot-revert lab-ubuntu clean-install
```
- **VirtualBox/VMware Workstation:** easiest desktop use; snapshots, shared folders (disable for hostile samples), NAT/host-only networks.
- **Proxmox VE:** a home-lab or small-server hypervisor with web UI, VMs + LXC containers, backups, clustering.
- **Hyper-V:** built into Windows Pro; good for Windows labs.
- Practices: snapshot before risky work, template/golden images, thin provisioning, keep guest tools updated, avoid nested virtualization unless needed (slower), encrypt disks for sensitive data.

## 4. GPU access and virtualization

- **Containers with GPUs:** install the NVIDIA driver and NVIDIA Container Toolkit, then `docker run --gpus all ...` (or `--gpus device=0`). The container needs a compatible CUDA runtime; the driver stays on the host.
- **VM GPU passthrough (VFIO/PCIe):** dedicate a whole GPU to a VM via IOMMU (enable VT-d/AMD-Vi, bind the GPU to `vfio-pci`); near-native performance, one VM per GPU.
- **vGPU/MIG:** NVIDIA vGPU shares a GPU among VMs (licensed); **MIG** partitions supported datacenter GPUs (A100/H100) into isolated slices; **time-slicing** shares a GPU in Kubernetes without isolation.
- **WSL2:** Linux with GPU support on Windows for development.
- Practices: pin CUDA/cuDNN/driver compatibility in docs, monitor with `nvidia-smi`/DCGM, set memory limits to avoid one job starving others, checkpoint long jobs, prefer batch queues for training.

## 5. Kubernetes basics for AI workloads

Core objects: Pod, Deployment (stateless services), StatefulSet, Job/CronJob (training, batch), Service/Ingress, ConfigMap/Secret, PersistentVolumeClaim, HorizontalPodAutoscaler. GPU scheduling: device plugin, `resources.limits: nvidia.com/gpu: 1`, node selectors/taints for GPU nodes. Model serving: KServe, Triton, vLLM behind a Service with autoscaling on queue depth or custom metrics; use PodDisruptionBudgets and readiness probes that wait for model load.
```yaml
apiVersion: apps/v1
kind: Deployment
metadata: { name: llm-serve }
spec:
  replicas: 1
  selector: { matchLabels: { app: llm-serve } }
  template:
    metadata: { labels: { app: llm-serve } }
    spec:
      containers:
        - name: server
          image: registry.example/llm-serve:1.0
          resources: { limits: { nvidia.com/gpu: 1, memory: 24Gi }, requests: { cpu: "4", memory: 16Gi } }
          readinessProbe: { httpGet: { path: /health, port: 8000 }, initialDelaySeconds: 60 }
          securityContext: { runAsNonRoot: true, allowPrivilegeEscalation: false }
```
Start without Kubernetes (single host + Docker Compose); adopt it when you need multi-node scheduling, autoscaling, or standardized operations.

## 6. Sandboxing untrusted code and AI tools

Threats: model-generated or user-submitted code reading secrets, calling the network, consuming resources, or escaping isolation.
Layered defense: (1) run in an ephemeral container or microVM per execution; (2) no network by default or an egress allow-list; (3) read-only root filesystem, a small writable tmpfs, no host mounts; (4) drop all capabilities, non-root, seccomp/AppArmor profile, `--pids-limit`; (5) CPU, memory, disk, and wall-clock limits; (6) no secrets in the environment; (7) log inputs/outputs and destroy the sandbox after use. Use stronger isolation (gVisor/Kata/Firecracker/VM) for multi-tenant or hostile code. Treat model output and downloaded artifacts as untrusted; never `pickle.load` untrusted files.
```bash
docker run --rm --network none --read-only --tmpfs /tmp:rw,size=64m --cap-drop ALL --pids-limit 64 \
  --memory 256m --cpus 0.5 --security-opt no-new-privileges -v "$PWD/job:/job:ro" python:3.11-slim \
  timeout 10 python /job/run.py
```

## 7. Lab design (security and AI)

- **Isolated network:** host-only or internal virtual networks; no bridge to production; a separate management interface; snapshots as the reset mechanism.
- **Defensive/analysis lab:** analysis VMs without shared folders or clipboard, host firewall rules blocking outbound unless explicitly needed, a logging VM collecting traffic and endpoint telemetry, golden images re-created regularly. Work only with samples and targets you are authorized to handle; follow the legal rules of your jurisdiction and the platform you train on.
- **Training labs (CTF/HackTheBox/TryHackMe style):** one VM for tooling, VPN into the platform, per-challenge snapshots, notes and screenshots stored outside the VM.
- **AI experiments:** separate GPU workstation or cloud instances; one environment per project (container or conda); data mounted read-only; cost alarms.
- **Reproducibility:** document the lab as code (Vagrantfile, Packer templates, Ansible/cloud-init, docker-compose) so it can be rebuilt in minutes.

## 8. Reproducible environments

Dev containers (`.devcontainer/devcontainer.json`), `uv`/`pip-tools`/`poetry` lock files, conda environment files, Nix flakes, Vagrant for VM-based setups, and Makefile targets (`make setup`, `make test`). Record the exact versions (Python, CUDA, drivers, OS) in the README. The rule: a new machine should reach a working state with a single documented command.

## 9. Networking and storage

Networking: bridge vs NAT vs host-only vs overlay; DNS inside containers; expose only needed ports; reverse proxy with TLS (Caddy/nginx/Traefik); service-to-service auth. Storage: volumes for state, bind mounts for dev, object storage for datasets and checkpoints, snapshots and backups for VMs, avoid storing data inside container layers.

## 10. Cost and operations

Right-size VMs and GPUs; schedule shutdowns for dev environments; use spot instances for fault-tolerant training; image and layer caching; monitor utilization (CPU, memory, GPU) and set autoscaling bounds; tag resources by project; keep a patch cadence for hosts, base images, and hypervisors.

## 11. Verification

On the user's machine: build and run the container, check it runs as non-root, confirm limits (`docker inspect`), confirm no network when `--network none`, run `trivy` on the image, snapshot and revert a VM, run `nvidia-smi` inside a GPU container. Mark all of these **open gap** in the sandbox and list the commands to run.
