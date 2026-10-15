import sys
import os
import random
import uuid
from datetime import datetime, timedelta, timezone

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, init_db
from app.models import User, Transaction, WorkloadMetric, ScalingDecision
from app.utils.security import hash_password


def seed_database():
    print("=" * 60)
    print("Seeding Synthetic Festival E-Commerce & Telemetry Data")
    print("=" * 60)

    init_db()
    db = SessionLocal()

    try:
        # 1. Seed Users
        print("[*] Seeding Users...")
        sample_users = [
            ("khushi@festival.com", "Khushi Agarwal", "password123"),
            ("arpita@festival.com", "Arpita Sinha", "password123"),
            ("ivy@festival.com", "Ivy Gupta", "password123"),
            ("rahul.sharma@example.com", "Rahul Sharma", "password123"),
            ("priya.patel@example.com", "Priya Patel", "password123"),
            ("amit.kumar@example.com", "Amit Kumar", "password123"),
            ("sneha.singh@example.com", "Sneha Singh", "password123"),
            ("vikram.mehta@example.com", "Vikram Mehta", "password123"),
            ("ananya.das@example.com", "Ananya Das", "password123"),
            ("rohit.verma@example.com", "Rohit Verma", "password123"),
        ]

        created_users = []
        for email, full_name, raw_pwd in sample_users:
            existing = db.query(User).filter_by(email=email).first()
            if not existing:
                u = User(
                    email=email,
                    full_name=full_name,
                    hashed_password=hash_password(raw_pwd),
                    is_active=True
                )
                db.add(u)
                created_users.append(u)
            else:
                created_users.append(existing)

        db.commit()
        for u in created_users:
            db.refresh(u)
        print(f"[+] {len(created_users)} users ready.")

        # 2. Seed Transactions (Festival Flash Sale Orders)
        print("[*] Seeding Festival Transactions...")
        products = [
            ("Diwali Special Smart LED TV 55-inch", 44999.00),
            ("Smartphone Pro Max 256GB", 69999.00),
            ("Wireless Noise Cancelling Headphones", 8499.00),
            ("Smart Fitness Watch Series 9", 15999.00),
            ("Festival Gourmet Sweets & Dry Fruits Box", 1499.00),
            ("Traditional Silk Designer Kurta", 2999.00),
            ("Gaming Laptop 16GB RTX 4060", 82999.00),
            ("Fast Charging Power Bank 20000mAh", 1899.00),
            ("Home Air Purifier HEPA 13", 11499.00),
            ("Robotic Vacuum Cleaner Pro", 24999.00)
        ]
        payment_methods = ["upi", "credit_card", "debit_card", "net_banking"]

        tx_count = 0
        now = datetime.now(timezone.utc)
        for i in range(60):
            user = random.choice(created_users)
            prod_name, prod_price = random.choice(products)
            order_time = now - timedelta(minutes=random.randint(1, 720))
            order_id = f"ORD-FEST-{uuid.uuid4().hex[:8].upper()}"

            tx = Transaction(
                user_id=user.id,
                order_id=order_id,
                product=prod_name,
                amount=prod_price * random.choice([1, 1, 1, 2]),
                items_count=random.randint(1, 3),
                payment_method=random.choice(payment_methods),
                status=random.choices(["completed", "pending", "failed"], weights=[90, 7, 3])[0],
                created_at=order_time
            )
            db.add(tx)
            tx_count += 1

        db.commit()
        print(f"[+] {tx_count} festival flash sale transactions seeded.")

        # 3. Seed Workload Telemetry (Simulating Festival Traffic Surge Progression)
        print("[*] Seeding Workload Telemetry Time-Series...")
        # 4 stages: baseline, ramping, peak surge, post-scale equilibrium
        base_time = now - timedelta(hours=3)
        metrics_seeded = 0

        for step in range(90):
            t = base_time + timedelta(minutes=step * 2)

            if step < 25:
                # Normal baseline traffic
                cpu = random.uniform(20.0, 38.0)
                mem = random.uniform(30.0, 45.0)
                req_rate = random.uniform(15.0, 40.0)
                latency = random.uniform(110.0, 190.0)
                instances = 2
                err = random.uniform(0.0, 0.2)
            elif step < 50:
                # Flash sale opens: Traffic surge begins
                progress = (step - 25) / 25.0
                cpu = 40.0 + progress * 48.0 + random.uniform(-4.0, 4.0)
                mem = 45.0 + progress * 40.0 + random.uniform(-3.0, 3.0)
                req_rate = 50.0 + progress * 350.0 + random.uniform(-20.0, 20.0)
                latency = 200.0 + progress * 950.0 + random.uniform(-50.0, 50.0)
                instances = 2 if progress < 0.6 else 4
                err = progress * 2.5
            elif step < 75:
                # Peak festival sale with RL Auto-scaling reacting
                instances = 8
                cpu = random.uniform(62.0, 74.0)
                mem = random.uniform(65.0, 78.0)
                req_rate = random.uniform(380.0, 500.0)
                latency = random.uniform(220.0, 340.0)
                err = random.uniform(0.0, 0.5)
            else:
                # Post-sale cooldown
                instances = 4
                cpu = random.uniform(35.0, 48.0)
                mem = random.uniform(40.0, 55.0)
                req_rate = random.uniform(80.0, 140.0)
                latency = random.uniform(140.0, 210.0)
                err = 0.0

            wm = WorkloadMetric(
                timestamp=t,
                cpu_percent=round(cpu, 2),
                memory_percent=round(mem, 2),
                request_rate=round(req_rate, 2),
                response_time_ms=round(latency, 2),
                instance_count=instances,
                error_rate=round(err, 2)
            )
            db.add(wm)
            metrics_seeded += 1

        db.commit()
        print(f"[+] {metrics_seeded} telemetry metric data points seeded.")

        # 4. Seed Scaling Decisions Audit Log
        print("[*] Seeding RL Scaling Decisions...")
        scaling_events = [
            ("maintain", 2, 2, "Cluster operating in normal baseline traffic.", 0.88, 0.95),
            ("scale_up", 2, 4, "Early traffic surge detected: CPU > 75%, Latency rising to 450ms.", 0.93, 0.90),
            ("scale_up", 4, 8, "Flash sale flood: Request rate 420 req/s, Response latency > 800ms.", 0.96, 0.94),
            ("maintain", 8, 8, "SLA restored: Latency stabilized at 280ms under 8 active instances.", 0.91, 0.98),
            ("scale_down", 8, 4, "Flash sale surge subsiding: CPU dropped to 34%, latency 180ms.", 0.87, 0.92),
        ]

        dec_count = 0
        for i, (action, curr, desired, reason, conf, reward) in enumerate(scaling_events):
            dec_time = base_time + timedelta(minutes=20 + i * 25)
            sd = ScalingDecision(
                timestamp=dec_time,
                action=action,
                current_instances=curr,
                desired_instances=desired,
                reason=reason,
                confidence=conf,
                triggered_by="rl_agent",
                feedback_reward=reward
            )
            db.add(sd)
            dec_count += 1

        db.commit()
        print(f"[+] {dec_count} RL scaling decisions seeded.")

        print("=" * 60)
        print("[SUCCESS] All synthetic festival data seeded successfully!")
        print("=" * 60)

    except Exception as exc:
        db.rollback()
        print(f"[ERROR] Seeding failed: {exc}")
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
