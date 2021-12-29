import sys
from distutils.util import strtobool

import torch
from redis import Redis
from rlgym.envs import Match
from rlgym.utils.reward_functions.common_rewards import ConstantReward

from rocket_learn.rollout_generator.redis_rollout_generator import RedisRolloutWorker
from training.learner import WORKER_COUNTER
from training.obs import NectoObsBuilder
from training.parser import NectoAction
from training.reward import NectoRewardFunction
from training.state import NectoStateSetter
from training.terminal import NectoTerminalCondition


def get_match(r, force_match_size, constant_reward=False):
    order = (1, 2, 3, 1, 1, 2, 1, 1, 3, 2, 1)  # Close as possible number of agents
    # order = (1, 1, 2, 1, 1, 2, 3, 1, 1, 2, 3)  # Close as possible with 1s >= 2s >= 3s
    # order = (1,)
    team_size = order[r % len(order)]
    if force_match_size:
        team_size = force_match_size

    return Match(
        # reward_function=CombinedReward.from_zipped(
        #     (DiffReward(LiuDistancePlayerToBallReward()), 0.05),
        #     (DiffReward(LiuDistanceBallToGoalReward()), 10),
        #     (EventReward(touch=0.05, goal=10)),
        # ),
        # reward_function=NectoRewardFunction(goal_w=0, shot_w=0, save_w=0, demo_w=0, boost_w=0),
        reward_function=NectoRewardFunction(),
        terminal_conditions=NectoTerminalCondition(),
        obs_builder=NectoObsBuilder(),
        action_parser=NectoAction(),
        state_setter=NectoStateSetter(),
        self_play=True,
        team_size=team_size,
    )


def make_worker(host, name, password, limit_threads=True, send_gamestates=False, force_match_size=None):
    if limit_threads:
        torch.set_num_threads(1)
    r = Redis(host=host, password=password)
    w = r.incr(WORKER_COUNTER) - 1
    return RedisRolloutWorker(r, name,
                              match=get_match(w, force_match_size, constant_reward=send_gamestates),
                              current_version_prob=.5,
                              send_gamestates=send_gamestates)


def main():
    # if not torch.cuda.is_available():
    #     sys.exit("Unable to train on your hardware, perhaps due to out-dated drivers or hardware age.")

    assert len(sys.argv) >= 5  # last is optional to force match size

    force_match_size = None

    print(len(sys.argv))
    if len(sys.argv) == 5:
        _, name, ip, password, compress = sys.argv
    else:
        _, name, ip, password, compress, force_match_size = sys.argv
        force_match_size = int(force_match_size)

        if force_match_size > 3 or force_match_size < 1:
            force_match_size = None

    try:
        worker = make_worker(ip, name, password, limit_threads=True, send_gamestates=bool(strtobool(compress)),
                             force_match_size=force_match_size)
        worker.run()
    finally:
        print("Problem Detected. Killing Worker...")


if __name__ == '__main__':
    main()
