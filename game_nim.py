"""Haakon8855"""


class GameNim:
    """
    Implementation of the NIM game as a simworld.
    """

    def __init__(self, num_pieces: int = 10, max_take: int = 2):
        self.num_pieces = num_pieces  # N, number of pieces on the board
        self.max_take = max_take  # K, maximium amount of pieces allowed to take

    def get_initial_state(self):
        """
        Returns the initial state of the game.
        State is represented as (number of remaining pieces, pid of next player to move (0 or 1))
        """
        return self.get_one_hot_from_state((self.num_pieces, 0))

    def get_state_size(self):
        """
        Returns the length of the state vector.
        """
        return len(self.get_initial_state())

    def get_move_size(self):
        """
        Returns the length of the move vector.
        """
        return 1

    def get_legal_actions(self, state):
        """
        Returns all allowed actions from current state.
        """
        num_discs = self.get_num_discs_from_one_hot(state)
        return list(range(1, min(num_discs, self.max_take) + 1))

    def get_child_state(self, state, action: int):
        """
        Makes a move by removing the specified amount of pieces from the board.
        Parameters:
            int action: Number of pieces to remove from the board
        Exceptions:
            Throws ValueError if action is not within legal parameters
        """
        num_discs = self.get_num_discs_from_one_hot(state)
        if action < 1 or action > self.max_take:
            raise ValueError(f"""Given action not within legal parameters.
                 Must be greater than 1 and less than the maximium allowed
                 pieces to take ({self.max_take})""")
        if action > num_discs:
            raise ValueError(f"""Given action not within legal parameters.
                 Must be greater than 1 and less than the current number 
                 of pieces ({self.max_take})""")
        child_state_pieces = num_discs - action
        child_state_pid = 1 - state[-1]
        return (child_state_pieces, child_state_pid)

    def get_all_child_states(self, state):
        """
        Returns all child states and the action to reach it from the given state.
        """
        actions = self.get_legal_actions(state)
        action_state_pairs = []
        for action in actions:
            action_state_pairs.append(
                (action, self.get_child_state(state, action)))

    def state_is_final(self, state):
        """
        Returns a boolean for whether the given state is a goal state or not.
        """
        return state[0] == 1

    def p0_to_play(self, state):
        """
        Returns True if the next player is pid, False otherwise.
        """
        return state[-1] == 0

    def winner_is_p0(self, state):
        """
        Return 1 if the winner of this game is player 1, -1 otherwise.
        """
        return self.state_is_final(state) and not self.p0_to_play(state)

    def get_one_hot_from_state(self, state_num):
        """
        Returns a one-hot encoded vector of the state given the state.
        """
        pid = state_num[1]  # Extract the pid
        curr_discs = state_num[0]  # Get the current amount of remaining discs
        state_oh = [0] * (self.num_pieces + 1)  # Create a list of zeros
        state_oh[curr_discs] = 1  # Set the correct index's value to 1
        state_oh.append(pid)  # Append the pid to the end
        return state_oh

    def get_num_discs_from_one_hot(self, state_oh):
        """
        Returns the number of remaining discs given a one-hot encoded state.
        """
        state_oh = state_oh[:-1]  # Remove pid
        curr_discs = state_oh.index(1)  # Get index of the 1 in the vector
        return curr_discs

    def __str__(self):
        return f"N = {self.num_pieces}, K = {self.max_take}"


def main():
    """
    Main function for running this python script.
    """
    simworld = GameNim(num_pieces=10, max_take=4)
    print(simworld)
    state = simworld.get_initial_state()
    print(simworld.get_legal_actions(state))
    print(simworld.get_legal_actions(10))


if __name__ == "__main__":
    main()
