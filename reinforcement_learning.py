"""Haakon8855"""

import numpy as np

from monte_carlo_ts import MonteCarloTreeSearch
from actor_network import ActorNetwork


class ReinforcementLearner():
    """
    A reinforcement learning algorithm implementing Monte Carlo Tree Search
    (MCTS) to train the default policy (in this case an ANN).
    """

    def __init__(self,
                 sim_world,
                 actor_network,
                 mcts,
                 num_policies: int = 5,
                 weights_path: str = "model/actor_var_start/",
                 num_games: int = 100,
                 epsilon: float = 0.1,
                 batch_size: int = 200):
        self.num_policies = num_policies
        self.num_games = num_games
        self.rbuf_distributions = []
        self.rbuf_states = []
        self.epsilon = epsilon
        self.batch_size = batch_size

        self.sim_world = sim_world
        self.actor_network = actor_network
        self.mcts = mcts

        self.weights_path = weights_path + self.sim_world.identifier
        self.save_count = 0
        self.initialize_actor_network()
        self.initialize_mcts()

    def initialize_actor_network(self):
        """
        Initializes the actor network with the correct input
        and output parameters.
        """
        input_size = self.sim_world.get_state_size()
        output_size = self.sim_world.get_move_size()
        self.actor_network = ActorNetwork(input_size, output_size,
                                          self.sim_world, self.weights_path)

    def initialize_mcts(self):
        """
        Initializes monte carlo tree search with the correct parameters.
        """
        self.mcts = MonteCarloTreeSearch(board=self.sim_world,
                                         default_policy=self.actor_network)

    def train(self):
        """
        Runs the traning algorithm to train the default policy neural network
        mapping states to actions.
        """
        weights_loaded = self.actor_network.load_weights(self.save_count)
        if weights_loaded:
            return
        # Save initial weights to file
        self.actor_network.save_weights(self.save_count)
        self.save_count += 1
        # Clear replay buffer RBUF
        self.rbuf_distributions = []
        self.rbuf_states = []
        # Randomly init ANET - Done
        # for game in num_games
        for i in range(self.num_games):
            # s_init <- starting_board_state
            state = self.sim_world.get_initial_state()
            # self.sim_world.show_visible_board(state)
            self.mcts.initialize_variables()
            while not self.sim_world.state_is_final(state):
                # Initialize mcts to a single root which represents s_init
                # and run a simulated game from the root state.
                try:
                    action, distribution = self.mcts.mc_tree_search(state)
                except ValueError:
                    print("BROKE1")
                    break
                # Append distribution to RBUF
                self.rbuf_distributions.append(distribution)
                self.rbuf_states.append(state)
                # Choose actual move from D
                chosen_action_index = np.argmax(distribution)
                if np.random.random() < self.epsilon:
                    # Choose one random legal action
                    # Copy distribution
                    random_distribution = distribution.copy()
                    # Set all probabilities larger than 0 to 1
                    random_distribution[random_distribution > 0] = 1
                    # Normalize vector to choose uniformly between legal actions
                    random_distribution = random_distribution / random_distribution.sum(
                    )
                    chosen_action_index = np.random.choice(
                        len(random_distribution), 1, p=random_distribution)[0]
                action = self.sim_world.get_one_hot_action(chosen_action_index)
                # Perform chosen action
                state = self.sim_world.get_child_state(state, action)
                # self.sim_world.show_visible_board(state)

            # Train ANET on random minibatch of cases from RBUF
            self.train_actor_network()
            print(f"Episode {i}")
            if i % (self.num_games // (self.num_policies - 1)) == 0 and i != 0:
                self.actor_network.save_weights(self.save_count)
                self.save_count += 1
        self.actor_network.save_weights(self.save_count)
        self.save_count += 1

    def train_actor_network(self):
        """
        Trains the actor network on a minibatch of cases from RBUF.
        """
        # random_indices = np.random.default_rng().choice(
        #     len(self.rbuf_distributions),
        #     min(self.batch_size, len(self.rbuf_distributions)),
        #     replace=False)
        # minibatch_states = np.array(self.rbuf_states)[random_indices]
        # minibatch_distr = np.array(self.rbuf_distributions)[random_indices]
        # self.actor_network.fit(train_x=np.array(minibatch_states),
        #                        train_y=np.array(minibatch_distr),
        #                        epochs=100)
        self.actor_network.fit(train_x=np.array(self.rbuf_states),
                               train_y=np.array(self.rbuf_distributions),
                               epochs=100)

    def test_nim(self):
        """
        Tests the trained nim policy.
        """
        for i in range(1, self.sim_world.num_pieces + 1):
            state = self.sim_world.get_one_hot_state((i, 0))
            # Print state
            num_state = self.sim_world.get_num_discs_from_one_hot(state)
            print(f"State: {num_state}")
            # Find move
            action, distr = self.actor_network.propose_action(
                state, get_distribution=True)
            # Print move
            print(f"Proposed action: {action}")
            print(f"Proposed action distribution: {distr}")

    def test_hex(self):
        """
        Tests the trained hex policy.
        """
        state = self.sim_world.get_initial_state()
        print(f"Board:\n{self.sim_world.get_board_readable(state)}\n")
        while not self.sim_world.state_is_final(state):
            action, distr = self.actor_network.propose_action(
                state, get_distribution=True)
            print(f"Proposed action: {action}")
            print(f"Proposed action distribution: {distr}")
            state = self.sim_world.get_child_state(state, action)
            final, winner = self.sim_world.state_is_final(state,
                                                          get_winner=True)
            print(f"Final state = {final}, winner pid = {winner}")
            print(f"Board:\n{self.sim_world.get_board_readable(state)}\n")

    def play_hex(self):
        """
        Play hex agains the machine.
        """
        weights_loaded = self.actor_network.load_weights(15)
        if not weights_loaded:
            print("Could not load weights, returning")
            return
        state = self.sim_world.get_initial_state()
        print(f"Board:\n{self.sim_world.get_board_readable(state)}\n")
        self.sim_world.show_visible_board(state)
        while not self.sim_world.state_is_final(state):

            action, distr = self.actor_network.propose_action(
                state, get_distribution=True)
            print(f"Proposed action: {action}")
            print(f"Proposed action distribution: {distr}")
            state = self.sim_world.get_child_state(state, action)
            final, winner = self.sim_world.state_is_final(state,
                                                          get_winner=True)
            print(f"Final state = {final}, winner pid = {winner}")
            print(f"Board:\n{self.sim_world.get_board_readable(state)}\n")
            self.sim_world.show_visible_board(state)
            if final:
                break

            legal_actions = self.sim_world.get_legal_actions(
                self.sim_world.get_initial_state())
            user_action = int(input("Please select action: "))
            state = self.sim_world.get_child_state(state,
                                                   legal_actions[user_action])
            final, winner = self.sim_world.state_is_final(state,
                                                          get_winner=True)
            print(f"Final state = {final}, winner pid = {winner}")
            print(f"Board:\n{self.sim_world.get_board_readable(state)}\n")
            self.sim_world.show_visible_board(state)
