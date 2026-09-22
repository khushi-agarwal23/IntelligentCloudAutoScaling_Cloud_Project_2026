# Intelligent Cloud Auto-Scaling Framework for E-Commerce Festival Sales Using Reinforcement Learning

## Team Members

Khushi Agarwal

Arpita Sinha

Ivy Gupta

---

## Problem Statement
Current cloud auto-scaling techniques rely on fixed threshold rules, which are not effective in handling sudden traffic spikes during e-commerce festival sales. This can lead to increased response time, server failures, poor user experience, and higher cloud costs. The project proposes an intelligent Reinforcement Learning-based auto-scaling framework on AWS that dynamically adjusts cloud resources according to real-time workload, ensuring better performance, reliability, and cost efficiency.


---

## Objectives
1.    To design an intelligent cloud auto-scaling framework for e-commerce platforms that can efficiently handle sudden traffic surges during festival sales.
2.    To develop a reinforcement learning-based resource allocation strategy that dynamically adjusts cloud resources according to real-time workload conditions.
3.    To optimize cloud resource utilization by minimizing over-provisioning and under-provisioning while maintaining application performance.
4.    To reduce response time and ensure high availability during peak shopping periods through adaptive scaling decisions.
5.    To evaluate the proposed framework by comparing its performance with conventional threshold-based or reactive auto-scaling techniques using metrics such as response time, resource utilization, scaling latency, and operational cost.



---

## Proposed Architecture
The proposed system uses an AWS-based intelligent cloud architecture to automatically manage cloud resources during high-traffic e-commerce events. User requests are first routed through an Elastic Load Balancer (ELB), which distributes traffic among multiple Amazon EC2 instances. The application continuously monitors performance metrics such as CPU utilization, memory usage, request rate, and response time using Amazon CloudWatch.

These monitoring metrics are provided to a Reinforcement Learning (RL) agent, which analyzes the current system state and decides whether to increase, decrease, or maintain the number of active cloud instances. Based on the RL agent's decision, the Auto Scaling Group automatically launches or terminates EC2 instances to efficiently handle the workload. User and transaction data are stored in Amazon RDS, while logs, static files, and trained models are stored in Amazon S3.


---

## Technology Stack

- Python
- AWS
- Reinforcement Learning
- Amazon EC2
- CloudWatch
- Auto Scaling
- Lambda
- S3
- SageMaker

---

## Dataset

(To be finalized)