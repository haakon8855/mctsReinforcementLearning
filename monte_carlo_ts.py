"""Haakon8855"""

import numpy as np


class MonteCarloTreeSearch:
    """
    Class for running Monte Carlo Tree search on a simworld.
    """

    def __init__(self,
                 board,
                 default_policy,
                 simulations: int = 500,
                 default_exp_const: int = 1):
        self.board = board  # Of type simworld
        self.epsilon = 0.1
        self.default_policy = default_policy
        self.default_exp_const = default_exp_const
        self.simulations = simulations  # M-value for number of simulations
        self.state = None
        self.tree = set()
        self.heuristic = {}
        self.visit_counts_s = {}
        self.visit_counts_sa = {}

    def initialize_variables(self):
        """
        Resets the variables to their initial state.
        """
        self.tree = set()
        self.heuristic = {}
        self.visit_counts_s = {}
        self.visit_counts_sa = {}

    def mc_tree_search(self, root_state):
        """
        Performs MCTS for self.simulations number of times. Each resulting in
        a new node in the tree being created.
        """
        for _ in range(self.simulations):
            self.simulate(root_state)  # Run simulation from root state
        self.state = root_state
        # Return an action and the distribution from the root state
        return self.select_action(root_state,
                                  0), self.get_visited_distribution(root_state)

    def simulate(self, root_state):
        """
        Simulates one run of the game from the root state. Walks down the tree
        and performs rollout if a leaf node is reached before the simulated
        game is over.
        """
        self.state = root_state
        # Go down the tree
        visited_states, performed_actions = self.simulate_tree()
        # Run rollout after leaf-node is reached
        outcome, first_action = self.simulate_default()
        if first_action is not None:
            performed_actions.append(first_action)
        # Run backup on the tree after rollout has reached final state
        self.backup(visited_states, performed_actions, outcome)

    def simulate_tree(self):
        """
        Simulates the walk of moves down the tree itself.
        """
        exploration = self.default_exp_const
        visited_states = []  # Keep track of visited tree-nodes
        performed_actions = []
        while not self.board.state_is_final(self.state):
            state_t = self.state
            visited_states.append(state_t)
            # If state is leaf-node add it to the tree
            if state_t not in self.tree:
                self.new_node(state_t)
                return visited_states, performed_actions
            # Else, keep going down the tree by doing moves
            action = self.select_action(state_t, exploration)
            performed_actions.append(action)
            self.state = self.board.get_child_state(self.state, action)
        return visited_states, performed_actions

    def simulate_default(self):
        """
        Simulates the rollout of default moves after a leaf node in the tree
        is reached. The default policy is used to determine the moves.
        Returns the first move performed by the ANET, in order for backup to
        work properly.
        """
        # Use ANET to play game until a final state is reached.
        first_action = None
        if not self.board.state_is_final(self.state):
            first_action = self.default_policy.propose_action(
                self.state, epsilon=self.epsilon)
            self.state = self.board.get_child_state(self.state, first_action)
        while not self.board.state_is_final(self.state):
            action = self.default_policy.propose_action(self.state,
                                                        epsilon=self.epsilon)
            self.state = self.board.get_child_state(self.state, action)
        return self.board.winner_is_p0(self.state), first_action

    def select_action(self, state, exploration):
        """
        Selects an action to perform when walking down the tree. Actions never
        performed before, or actions which have been performed relatively few
        number of times are favoured.
        """
        legal_actions = self.board.get_legal_actions(state)
        action_values = []
        # Black to play, maximize reward
        if self.board.p0_to_play(state):
            for action in legal_actions:
                action_value = self.heuristic[
                    (state, action)] + exploration * np.sqrt(
                        np.log(self.visit_counts_s[state]) /
                        (self.visit_counts_sa[(state, action)] + 1))
                action_values.append(action_value)
            chosen_action_index = np.argmax(np.array(action_values))
            chosen_action = legal_actions[chosen_action_index]
        # Red to play, minimize reward
        else:
            for action in legal_actions:
                action_value = self.heuristic[
                    (state, action)] - exploration * np.sqrt(
                        np.log(self.visit_counts_s[state]) /
                        (self.visit_counts_sa[(state, action)] + 1))
                action_values.append(action_value)
            chosen_action_index = np.argmin(np.array(action_values))
            chosen_action = legal_actions[chosen_action_index]
        return chosen_action

    def backup(self, visited_states, performed_actions, outcome):
        """
        Runs the backup algorithm on the network to update the values along
        the nodes and paths based on the game's outcome.
        """
        for stat_act in zip(visited_states, performed_actions):
            self.visit_counts_s[
                stat_act[0]] = self.visit_counts_s[stat_act[0]] + 1
            self.visit_counts_sa[stat_act] = self.visit_counts_sa[stat_act] + 1
            self.heuristic[stat_act] = self.heuristic[stat_act] + (
                outcome -
                self.heuristic[stat_act]) / self.visit_counts_sa[stat_act]

    def new_node(self, state_t):
        """
        Creates a new node in the tree and sets all its values to 0.
        """
        self.tree.add(state_t)
        self.visit_counts_s[state_t] = 0
        legal_actions = self.board.get_legal_actions(state_t)
        for action in legal_actions:
            self.visit_counts_sa[(state_t, action)] = 0
            self.heuristic[(state_t, action)] = 0

    def get_visited_distribution(self, state):
        """
        Returns the visit counts along the exiting paths from the given state.
        """
        # Get all legal actions in state
        legal_actions = self.board.get_legal_actions(state)

        # Create a list of the visit counts along each action path
        visited_vector = []
        for action in legal_actions:
            visited_vector.append(self.visit_counts_sa[(state, action)])

        # Normalize the visit counts vector
        visited_vector = np.array(visited_vector, dtype=float)
        visited_vector /= visited_vector.sum()

        # Return the distribution of visit counts as a list with length equal to
        # the total number of actions possible disregarding the current state.
        action_visited = np.zeros(len(legal_actions[0]))
        for i, action in enumerate(legal_actions):
            action_visited += visited_vector[i] * np.array(action)
        return action_visited
