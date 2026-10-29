# Reinforcement learning

*Last updated: 2026-10-13 | Version-sensitive: Stable-Baselines3/Gymnasium APIs; RLHF method names | Re-check current docs before pinning versions, prices, or API names.*

Learning to act from rewards. Covers concepts, algorithms, working tabular code, deep RL practice, RLHF-style alignment, reward design, and when not to use RL.

## Contents
1. When RL is the right tool
2. Concepts
3. Algorithm map
4. Tabular Q-learning (runs)
5. Deep RL practice (DQN, PPO)
6. Environments and simulators
7. Reward design
8. Exploration and stability
9. RL for games and bots
10. RL for language models (RLHF, DPO, GRPO)
11. Offline RL, bandits, and safe deployment
12. Debugging checklist
13. Verification

## 1. When RL is the right tool

Use RL when decisions are sequential, outcomes are delayed, you can simulate or safely interact many times, and no labeled "right action" data exists. Try first: heuristics, search (A*, MCTS), supervised imitation from demonstrations, and **contextual bandits** (single-step decisions with feedback, much simpler and often enough). RL is data-hungry, unstable, and sensitive to reward design; budget for simulation and evaluation.

## 2. Concepts

- **Agent, environment, state s, action a, reward r, policy π(a|s), episode.**
- **Return** `G = Σ γ^t r_t` (discount γ in 0.9-0.999). **Value** `V(s)` = expected return; **Q(s,a)** = expected return after action a.
- **Bellman equation:** `Q(s,a) = r + γ max_a' Q(s',a')`.
- **MDP:** states, actions, transition probabilities, rewards, discount. Partial observability (POMDP) needs memory (frame stacking, recurrent policies).
- **On-policy** (learn from the current policy: PPO, A2C) vs **off-policy** (replay old data: DQN, SAC, TD3).
- **Model-free** vs **model-based** (learn or use a dynamics model to plan: Dreamer, MuZero, MPC).
- **Exploration vs exploitation:** ε-greedy, entropy bonus, curiosity, optimism.

## 3. Algorithm map

| Setting | Start with |
|---|---|
| Small discrete states | Tabular Q-learning / SARSA |
| Discrete actions, pixels or vectors | DQN family (Double, Dueling, PER, Rainbow) |
| Continuous control | SAC or TD3 (off-policy), PPO (robust default) |
| General default | **PPO** (stable, simple, parallelizable) |
| Sparse rewards | Reward shaping, curriculum, hindsight replay, curiosity, demonstrations |
| Multi-agent | Self-play, MAPPO, population-based training |
| Planning with a simulator | MCTS, model predictive control |
| Static dataset only | Offline RL (CQL, IQL) or behavior cloning |
| Single-step choices | Bandits (UCB, Thompson sampling) |

## 4. Tabular Q-learning (runs)

```python
import numpy as np
rng = np.random.default_rng(0)
N = 5                                                    # 5x5 grid: start (0,0), goal (4,4), pit (2,2)
ACTIONS = [(-1, 0), (1, 0), (0, -1), (0, 1)]             # up, down, left, right
def step(s, a):
    r, c = s; dr, dc = ACTIONS[a]
    r2, c2 = min(N - 1, max(0, r + dr)), min(N - 1, max(0, c + dc))
    if (r2, c2) == (4, 4): return (r2, c2), 10.0, True
    if (r2, c2) == (2, 2): return (r2, c2), -10.0, True
    return (r2, c2), -0.1, False                         # small step cost encourages short paths
Q = np.zeros((N, N, 4)); alpha, gamma = 0.2, 0.95
def train(episodes=3000):
    for ep in range(episodes):
        eps = max(0.05, 1.0 - ep / (episodes * 0.6)); s = (0, 0)
        for _ in range(200):
            a = rng.integers(4) if rng.random() < eps else int(np.argmax(Q[s]))
            s2, r, done = step(s, a)
            Q[s][a] += alpha * (r + (0 if done else gamma * np.max(Q[s2])) - Q[s][a])   # Bellman update
            s = s2
            if done: break
def evaluate():
    s, ret, path = (0, 0), 0.0, [(0, 0)]
    for _ in range(50):
        s, r, done = step(s, int(np.argmax(Q[s]))); ret += r; path.append(s)
        if done: break
    return ret, path
train(); ret, path = evaluate()
print("return", round(ret, 1), "steps", len(path) - 1, "reached goal", path[-1] == (4, 4), "touched pit", (2, 2) in path)
```
Lessons embedded: epsilon decay, the terminal-state target has no bootstrap, step penalty shapes behavior, evaluate with a greedy policy separately from training.

## 5. Deep RL practice (DQN, PPO)

Libraries: Stable-Baselines3, CleanRL (single-file references), RLlib, Tianshou, Gymnasium environments. Typical PPO run (not run here):
```python
# pip install stable-baselines3 gymnasium
from stable_baselines3 import PPO
from stable_baselines3.common.env_util import make_vec_env
env = make_vec_env("CartPole-v1", n_envs=8)
model = PPO("MlpPolicy", env, n_steps=256, batch_size=256, learning_rate=3e-4, gamma=0.99, gae_lambda=0.95, clip_range=0.2, ent_coef=0.0, verbose=1)
model.learn(total_timesteps=200_000); model.save("ppo_cartpole")
```
Practice: normalize observations and rewards, run several seeds (results vary widely), log episode return, length, entropy, value loss, KL; evaluate on fixed seeds periodically; checkpoint the best; start with a tiny version of the task that must solve quickly to prove the pipeline.

## 6. Environments and simulators

Use the Gymnasium API (`reset() -> obs, info`; `step(a) -> obs, reward, terminated, truncated, info`). Custom environments: define observation/action spaces, make `step` fast (vectorize, avoid Python loops), seed everything, and unit-test dynamics and reward. Game engines (Unity ML-Agents, Godot RL, Unreal) provide rich simulators; headless mode and parallel instances give throughput. Sim-to-real: domain randomization (vary physics, visuals, noise), system identification, and conservative deployment.

## 7. Reward design

- Reward what you actually want, measurable and hard to game. Agents exploit loopholes ("reward hacking"): test by watching behavior, not only scores.
- Prefer sparse true goals plus **potential-based shaping** (`F = γΦ(s') − Φ(s)`) which preserves optimal policies.
- Keep reward scales sane (clip or normalize); balance multiple terms with weights tuned by evaluation; add penalties for energy/time/risk.
- Curriculum: start easy, increase difficulty as success crosses a threshold.
- Imitation + RL: pretrain with behavior cloning on demonstrations, then fine-tune.

## 8. Exploration and stability

Common failure causes: reward too sparse, bad scaling, learning rate too high, insufficient exploration, non-stationary data in off-policy buffers, bugs in terminal handling (time-limit truncation vs true termination), and train/eval mismatch. Fixes: entropy regularization, larger batches, target networks, gradient clipping, advantage normalization, smaller learning rates, more parallel environments, longer training. Average over seeds and use confidence intervals.

## 9. RL for games and bots

- First choose the simplest bot that meets the design goal: state machines, behavior trees, utility AI, A*/steering. RL bots are best for adaptive opponents, playtesting/balancing agents, and procedural content testing.
- Observation design: relative positions, velocities, raycasts instead of raw pixels; action space: discrete moves/shoot; keep episodes short with clear rewards (damage dealt, objectives, survival) and penalties for idling.
- Self-play with a league of past checkpoints avoids strategy cycling. Use RL agents to find exploits and measure difficulty curves (win rate vs designed AI).
- Ship a small distilled or rules-based policy if inference cost or predictability matters; keep human-like imperfections (reaction delay, aim error) for fun.

## 10. RL for language models (RLHF, DPO, GRPO)

- **SFT:** supervised fine-tuning on good demonstrations.
- **RLHF:** train a reward model from human preference comparisons, then optimize the policy with PPO plus a KL penalty to a reference model to prevent drift.
- **DPO / IPO / KTO:** optimize directly on preference pairs without an explicit reward model; simpler and stable.
- **GRPO and RL with verifiable rewards:** sample several answers per prompt, reward by an automatic checker (unit tests, math answer match, format), and use group-relative advantages. Works where correctness can be verified.
- Risks: reward hacking (verbosity, sycophancy), over-optimization, distribution shift. Keep held-out human evals and a KL/behavior budget.

## 11. Offline RL, bandits, and safe deployment

- **Offline RL** learns from logged data without interaction; needs conservative methods to avoid acting outside the data support; always compare with behavior cloning.
- **Bandits** for UI/pricing/recommendation experiments: Thompson sampling is a strong default.
- **Safe deployment:** run the learned policy in shadow mode first, bound its actions (action clipping, safety layers), keep a fallback controller, canary rollout, monitor reward and constraint violations, and keep a kill switch.

## 12. Debugging checklist

- [ ] Environment is correct (manual rollout, unit tests, reward at known states)
- [ ] A trivial policy gets the expected reward; a random policy baseline recorded
- [ ] Observations normalized; no leakage of future info; terminal vs truncation handled
- [ ] Learning curves across seeds; entropy not collapsing too early
- [ ] Policy behavior watched in replay, not just scored
- [ ] Hyperparameters changed one at a time; results table kept

## 13. Verification

Run the tabular example and confirm the goal is reached without the pit; compare against a random policy and a heuristic baseline; evaluate over multiple seeds; mark deep-RL training code **open gap** unless run.
