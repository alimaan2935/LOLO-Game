import json

import game_regular


class ObjectiveGame(game_regular.RegularGame):
    """Objective game of Lolo.

    Complete the objectives by joining tiles before moves run out"""

    GAME_NAME = 'Objective'

    def __init__(self):
        """Constructor

        Parameters:
            Parameters of the game are loaded from JSON file
        """

        # Load the JSON file
        self._file = 'objective.json'
        try:
            with open(self._file) as file:
                try:
                    self._data = json.load(file)
                except json.JSONDecodeError:
                    print("Failed to decode the json file")
        except IOError:
            print("Could not locate the file {}".format(self._file))

        # initialize the data
        self._min_group = self._data.get('min_group')
        self._size = self._data.get('size')
        self._types = self._data.get('types')
        self._objectives = self._data.get('objectives')
        self._moves = self._data.get('limit')

        # Call super and pass the loaded data into it
        super().__init__(size=self._size, types=self._types, min_group=self._min_group)

        # An instance of currently activated tile
        self.current_tile = None

    def check_objectives(self):
        """
        Check the objectives list and modify it if any of the objectives are met

        Return:
            bool(True): If any of the objective is met
            bool(False): if any exception occurs
        """

        for i in self._objectives[0]:
            x, y = i
            if y != 'Done':
                try:
                    if x == self.current_tile.get_type() and y <= self.current_tile.get_value()-1:
                        index = self._objectives[0].index(i)
                        self._objectives[0][index] = [x, 'Done']
                        return True
                except:
                    return False



    def activate(self, position):

        """Attempts to activate the tile at the given position.

        Parameters:
            position (tuple<int, int>): The position to activate.

        Yield:
            Yields None for each frame of drops and "DONE" when the dropping
            has finished.
        """
        # Reduce moves
        self._moves -= 1

        connected_cells = self._attempt_activate_collect(position)
        connected_cells.remove(position)

        self._resolving = True

        current = self.grid[position]
        self.current_tile = current

        connected_tiles = [self.grid[cell] for cell in connected_cells]

        # Join tiles
        current.join(connected_tiles)

        self.update_score_on_activate(current, connected_tiles)

        self._check_unlock_max(current)

        for cell in connected_cells:
            del self.grid[cell]

        yield from self.grid.replace_blanks()

        # Find tile, in case it moved.
        # Hack, but it works. Ideally above logic would indicate movement.
        position = self.find_tile_position(current)

        # Perform combo
        yield from self._explode_combo(position)

        # Final step
        yield "DONE"



        self._resolving = False
        self.emit('resolve')

        # Check for game over.
        if self.game_over():
            self.emit('game_over')
