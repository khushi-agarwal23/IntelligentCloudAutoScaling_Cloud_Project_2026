import sys
import os
import time
import random
import argparse
import httpx

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def run_simulation(base_url: str = "http://127.0.0.1:8000", rounds: int = 15, delay: float = 0.5):
    print("=" * 70)
    print("Intelligent Cloud Auto-Scaling: Festival Traffic Surge Simulator")
    print("=" * 70)
    print(f"Target Server: {base_url}")
    print(f"Rounds: {rounds}, Interval: {delay}s")
    print("=" * 70)

    products = [
        "Festival Flash Sale Phone 5G",
        "Diwali Festive Electronics Hamper",
        "Smart 4K UHD Television",
        "Bluetooth Noise Cancelling Earbuds"
    ]

    current_instances = 2

    # Check if target is a live server or if we should use in-memory TestClient
    live_server = False
    try:
        with httpx.Client(timeout=2.0) as client:
            resp = client.get(f"{base_url}/api/v1/health")
            if resp.status_code == 200:
                live_server = True
                print("[+] Connected to live server!")
    except Exception:
        print("[!] Live server not detected. Using internal FastAPI TestClient for simulation.")

    if not live_server:
        from fastapi.testclient import TestClient
        from app.main import app
        client = TestClient(app)
    else:
        client = httpx.Client(base_url=base_url, timeout=5.0)

    try:
        # Register a simulation user
        reg_resp = client.post(
            "/api/v1/auth/register",
            json={"email": f"sim_shopper_{random.randint(1000, 9999)}@sale.com", "password": "simpassword123", "full_name": "Flash Sale Tester"}
        )
        if reg_resp.status_code in [200, 201]:
            user_id = reg_resp.json().get("id")
        else:
            user_id = 1

        print(f"[+] Simulation shopper initialized (User ID: {user_id})")
        print("\nStarting Traffic Rounds...\n")

        for r in range(1, rounds + 1):
            # Simulate 3 phases: Baseline (rounds 1-4), Flash Sale Surge (rounds 5-11), Cooldown (rounds 12-15)
            if r <= 4:
                phase = "BASELINE"
                req_rate = random.uniform(15, 30)
                cpu = random.uniform(22, 35)
                mem = random.uniform(32, 42)
                latency = random.uniform(100, 160)
            elif r <= 11:
                phase = "FLASH-SALE SURGE"
                intensity = (r - 4) / 7.0
                req_rate = 120 + intensity * 450 + random.uniform(-20, 20)
                cpu = 65 + intensity * 28 + random.uniform(-3, 3)
                mem = 60 + intensity * 28 + random.uniform(-2, 2)
                latency = 350 + intensity * 900 + random.uniform(-40, 40)
            else:
                phase = "COOLDOWN"
                req_rate = random.uniform(40, 70)
                cpu = random.uniform(25, 38)
                mem = random.uniform(35, 48)
                latency = random.uniform(120, 200)

            # 1. Trigger Flash Sale Checkout
            checkout_res = client.post(
                "/api/v1/transactions/checkout",
                json={
                    "user_id": user_id,
                    "product": random.choice(products),
                    "amount": round(random.uniform(999.0, 49999.0), 2),
                    "items_count": random.randint(1, 3),
                    "payment_method": "upi"
                }
            )
            order_id = checkout_res.json().get("order_id", "N/A") if checkout_res.status_code == 201 else "FAIL"

            # 2. Ingest CloudWatch / ELB Telemetry Metric
            metric_payload = {
                "cpu_percent": round(cpu, 1),
                "memory_percent": round(mem, 1),
                "request_rate": round(req_rate, 1),
                "response_time_ms": round(latency, 1),
                "instance_count": current_instances,
                "error_rate": 0.0
            }
            metric_res = client.post("/api/v1/workload/metrics", json=metric_payload)

            # 3. Trigger RL Scaling Orchestrator (Evaluate-and-Act)
            eval_payload = {
                "cpu_percent": round(cpu, 1),
                "memory_percent": round(mem, 1),
                "request_rate": round(req_rate, 1),
                "response_time_ms": round(latency, 1),
                "current_instances": current_instances,
                "apply_to_aws": True
            }
            eval_res = client.post("/api/v1/scaling/evaluate-and-act", json=eval_payload)
            if eval_res.status_code == 200:
                eval_data = eval_res.json()
                decision = eval_data.get("decision", {})
                action = decision.get("action", "maintain")
                current_instances = decision.get("desired_instances", current_instances)
                conf = decision.get("confidence", 0.0)
            else:
                action = "error"
                conf = 0.0

            print(f"[{r:02d}/{rounds}] [{phase:^16}] Order: {order_id} | Req/s: {req_rate:5.1f} | CPU: {cpu:4.1f}% | Latency: {latency:6.1f}ms -> Decision: {action.upper():<10} (Instances: {current_instances}, Conf: {conf:.2f})")

            time.sleep(delay)

        print("\n" + "=" * 70)
        print("[SUCCESS] Traffic surge simulation complete!")
        # Fetch stats
        stats_res = client.get("/api/v1/transactions/stats")
        if stats_res.status_code == 200:
            s = stats_res.json()
            print(f"Final Stats: Total Orders={s.get('total_transactions')}, Revenue=₹{s.get('total_revenue'):,.2f}, AOV=₹{s.get('average_order_value'):,.2f}")
        print("=" * 70)

    finally:
        client.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate festival traffic spikes and evaluate auto-scaling.")
    parser.add_argument("--url", default="http://127.0.0.1:8000", help="Backend base URL")
    parser.add_argument("--rounds", type=int, default=12, help="Number of simulation rounds")
    parser.add_argument("--delay", type=float, default=0.2, help="Delay between rounds in seconds")
    args = parser.parse_args()

    run_simulation(base_url=args.url, rounds=args.rounds, delay=args.delay)
