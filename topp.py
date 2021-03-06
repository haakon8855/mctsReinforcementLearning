"""Haakon8855"""

import numpy as np
from matplotlib import pyplot as plt
from time import sleep

from actor_network import ActorNetwork


class Tournament():
    """
    Performs a tournament with the saved policies.
    """

    def __init__(self,
                 sim_world,
                 num_policies: int,
                 num_games_in_series: int,
                 weights_path: str,
                 network_layer_sizes: list,
                 network_layer_acts: list,
                 optimizer_str: str,
                 draw_board: bool = False):
        self.sim_world = sim_world
        self.num_policies = num_policies
        self.num_games_in_series = num_games_in_series
        self.weights_path = weights_path
        self.network_layer_sizes = network_layer_sizes
        self.network_layer_acts = network_layer_acts
        self.optimizer_str = optimizer_str
        self.draw_board = draw_board  # Whether to draw the board or not during TOPP
        self.animation_sleep_duration = 0.5  # Time to sleep between making a move

        self.policies = []
        self.policies_win_count = [0] * num_policies
        self.init_policies()

    def init_policies(self):
        """
        Loads all saved weights and saves the instances of ActorNetwork (policies).
        """
        for i in range(self.num_policies):
            input_size = self.sim_world.get_state_size()
            output_size = self.sim_world.get_move_size()
            save_path = self.weights_path + str(i)
            network = ActorNetwork(input_size, output_size, self.sim_world,
                                   save_path, self.network_layer_sizes,
                                   self.network_layer_acts, self.optimizer_str)
            network.load_weights()
            self.policies.append(network)

    def run(self):
        """
        Runs a tournament between the loaded policies.
        """
        for i in range(len(self.policies) - 1):
            for j in range(i + 1, len(self.policies)):
                self.play_one_series(i, j)
        print(f"Wins for each agent was: {self.policies_win_count}")
        self.plot_policies_win_count()

    def plot_policies_win_count(self):
        """
        Plots the win counts for each policy/agent.
        """
        plt.bar(np.arange(0, len(self.policies_win_count)),
                self.policies_win_count)
        plt.show()

    def play_one_series(self, index_a, index_b):
        """
        Plays one series between player at index_a and player at index_b,
        G games where each policy alternates playing as black.
        """
        players = [index_a, index_b]
        for _ in range(self.num_games_in_series):
            self.play_one_game(players[0], players[1])
            players.reverse()

    def play_one_game(self, index_0, index_1):
        """
        Play one hex game between two policies.
        """
        player_0 = self.policies[index_0]
        player_1 = self.policies[index_1]
        title = f"Agent {index_0} (black) vs. Agent {index_1} (red)"

        state = self.sim_world.get_initial_state()
        while True:
            # Black makes a move:
            action, distribution = player_0.propose_action(
                state, get_distribution=True)
            # Choose action randomly based on the output from the network
            distribution /= distribution.sum()
            distribution = distribution.copy()[0]
            action_num = np.random.choice(len(distribution), 1,
                                          p=distribution)[0]
            action = self.sim_world.get_one_hot_action(action_num)
            state = self.sim_world.get_child_state(state, action)
            if self.draw_board:
                self.sim_world.show_visible_board(state, title=title)
                sleep(self.animation_sleep_duration)
            final = self.sim_world.state_is_final(state)
            if final:
                self.policies_win_count[index_0] += 1
                return

            # Red makes a move:
            action, distribution = player_1.propose_action(
                state, get_distribution=True)
            # Choose action randomly based on the output from the network
            distribution /= distribution.sum()
            distribution = distribution.copy()[0]
            action_num = np.random.choice(len(distribution), 1,
                                          p=distribution)[0]
            action = self.sim_world.get_one_hot_action(action_num)
            state = self.sim_world.get_child_state(state, action)
            if self.draw_board:
                self.sim_world.show_visible_board(state, title=title)
                sleep(self.animation_sleep_duration)
            final = self.sim_world.state_is_final(state)
            if final:
                self.policies_win_count[index_1] += 1
                return
