import os
import sys

import torch
import wandb
from redis import Redis

from rocket_learn.ppo import PPO
from rocket_learn.rollout_generator.redis_rollout_generator import RedisRolloutGenerator
from training.agent import get_agent
from training.obs import NectoObsBuilder
from training.parser import NectoAction
from training.reward import NectoRewardFunction

WORKER_COUNTER = "worker-counter"

config = dict(
    seed=123,
    actor_lr=1e-4,
    critic_lr=1e-4,
    n_steps=1_000_000,
    batch_size=40_000,
    minibatch_size=10_000,
    epochs=35,
    gamma=0.995,
    iterations_per_save=10
)


if __name__ == "__main__":
    run_id = "obbbntaa"

    _, ip, password = sys.argv
    wandb.login(key=os.environ["WANDB_KEY"])
    logger = wandb.init(project="rocket-learn", entity="rolv-arild", id=run_id, config=config)
    torch.manual_seed(logger.config.seed)

    redis = Redis(host=ip, password=password)
    redis.delete(WORKER_COUNTER)  # Reset to 0


    def obs():
        return NectoObsBuilder()


    def rew():
        # return CombinedReward.from_zipped(
        #     (DiffReward(LiuDistancePlayerToBallReward()), 0.05),
        #     (DiffReward(LiuDistanceBallToGoalReward()), 10),
        #     (EventReward(touch=0.05, goal=10)),
        # )
        # return NectoRewardFunction(goal_w=0, shot_w=0, save_w=0, demo_w=0, boost_w=0)
        return NectoRewardFunction()

    def act():
        return NectoAction()

    rollout_gen = RedisRolloutGenerator(redis, obs, rew, act,
                                        save_every=logger.config.iterations_per_save,
                                        logger=logger, clear=run_id is None)

    agent = get_agent(actor_lr=logger.config.actor_lr, critic_lr=logger.config.critic_lr)

    alg = PPO(
        rollout_gen,
        agent,
        n_steps=logger.config.n_steps,
        batch_size=logger.config.batch_size,
        minibatch_size=logger.config.minibatch_size,
        epochs=logger.config.epochs,
        gamma=logger.config.gamma,
        logger=logger,
    )

    if run_id is not None:
        # alg.load("ppos/rocket-learn_1638479738.2639134/rocket-learn_1000/checkpoint.pt")
        alg.load("ppos/rocket-learn_1639878346.7736878/rocket-learn_680/checkpoint.pt")

    log_dir = "E:\\log_directory\\"
    repo_dir = "E:\\repo_directory\\"

    alg.run(iterations_per_save=logger.config.iterations_per_save, save_dir="ppos")
