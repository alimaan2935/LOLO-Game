"""
CSSE1001 Assignment 3
Semester 1, 2017
"""

import tkinter as tk
from tkinter import messagebox
import random
import pygame

import view
from base import BaseLoloApp
import highscores
import game_lucky7
import game_make13
import game_regular
import game_unlimited
import game_objective
import save_game
import model



__author__ = "Ali Nawaz Maan"
__email__ = "a.maan@uq.net.au"

__version__ = "1.0.0"


class LoloApp(BaseLoloApp):
    """
    Main class for Lolo Game --> Inherit from BaseLoloApp
    """
    def __init__(self, master, game=None, player_name=None, grid_view=None, default_score=0):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.
            game (model.AbstractGame): The game to play. Defaults to a
                                       game_regular.RegularGame.
            grid_view (view.GridView): The view to use for the game. Optional.

        """

        self._parent_frame = master
        self._player_name = player_name

        # Initialize the Logo Canvas and pack it
        self._logo = LoloLogo(master, width=400, height=110)
        self._logo.pack(side=tk.TOP, expand=True, anchor=tk.CENTER)

        # Initialize the Statusbar Frame and pack it
        self._statusbar = StatusBar(master)
        self._statusbar.pack(side=tk.TOP, fill=tk.X)
        self._statusbar.set_score(default_score)

        # Initialize inheritence from super class
        super().__init__(master, game, grid_view)

        # Display game mode on title bar of the window
        master.title('Lolo:: {} Game'.format(self._game.get_name()))

        # Initialize the menubar and pass the arguments
        self.menubar = tk.Menu(master)
        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="New Game", command=self.reset)
        menu.add_command(label="Save Game", command=self.save_game)
        menu.add_command(label="Exit", command=master.destroy)
        master.config(menu=self.menubar)

        # Bind keyboard events to implement keyboard shortcuts
        master.bind_all("<Control-n>", lambda x: self.reset())
        master.bind_all("<Control-l>", lambda x: self.lightning_effect())

        # Pass statusbar label with game mode
        self._statusbar.set_game(self._game)

        # Initialize the lightning button with default text and lightning attempts and pack it
        self._lights = 1
        self._lightning = tk.Button(master, text='Lightning OFF ({})'.format(self._lights),
                                    command=self.lightning_effect)
        self._lightning.pack(pady=5)
        self._light_toggle = False

        # Increasing lights :P
        self._prev_score = 0

        # Recording score
        self._high_scores = highscores.HighScoreManager(gamemode=self._game.get_name().lower())
        # Save game instance
        self._save_game = save_game.SaveLoadManager(gamemode=self._game.get_name().lower())

        self._game_over_grid = None

        # Objectives Grid
        if self._game.get_name() == 'Objective':
            self.objective_tiles()

        # icon of the game window
        pygame.init()
        icon = pygame.image.load('logo.jpg')
        pygame.display.set_icon(icon)

    def save_game(self):
        """
        Saving the current game by calling SavedGameManager instance
        """
        self._save_game.record(self._game.get_score(), self._game, self._player_name)

    def objective_tiles(self):
        """
        Draw grid of objective tiles onto the statusbar
        """

        # Frame for tiles
        self._objectives_frame = tk.Frame(self._statusbar)
        self._objectives_frame.pack()

        # draw the objective tile grid and pack it
        objectives = game_regular.RegularGame.deserialize(self._game._objectives)
        self._objective_view = view.GridView(self._objectives_frame, (1, len(self._game._objectives[0])))
        self._objective_view.pack(side=tk.RIGHT)

        self._objective_view.draw(objectives.grid, objectives.find_connections())

        self._moves_left = tk.Label(self._objectives_frame, text='Moves left: {}'.format(self._game._moves))
        self._moves_left.pack(side=tk.LEFT)

    def activate(self, position):
        """Attempts to activate the tile at the given position.

        Parameters:
            position (tuple<int, int>): Row-column position of the tile.

        Play:
            Sound for successful and invalid move.

        Return:
            Warning messegebox when activating an invalid tile.

        """

        # Checks for the available lightning
        if self._light_toggle:
            self.remove(position)
            self._lights -= 1
            self.lightning_effect()

        else:
            try:
                super().activate(position)
                sound = pygame.mixer.Sound("Sound.ogg")
                pygame.mixer.Sound.play(sound)

                # Check for objective game mode
                if self._game.get_name() == 'Objective':
                    if self._game.check_objectives():
                        # redraw the objective grid
                        self._objectives_frame.destroy()
                        self.objective_tiles()
                    self.obj_game_play()
                    # Emit game over if all of the objectives are met
                    if set([x[1] for x in self._game._objectives[0]]) == {'Done'}:
                        self._master.after(1000, lambda: self._game.emit('game_over'))



            except IndexError:
                sound = pygame.mixer.Sound("cant.ogg")
                pygame.mixer.Sound.play(sound)
                return messagebox.showwarning("Can't Activate",
                                              "Cannot activate position {}"
                                              .format(position))


    def obj_game_play(self):
        """
        Check the moves left in objective game mode and then call game over method afer a delay
         The delay is to let the grid resolve
        """

        if self._game._moves <= 0:
            self._master.after(1000, self.game_over)

        # Display remaining moves
        self._moves_left.config(text='Moves left: {}'.format(self._game._moves))



    def score(self, points):
        """Handles increase in score."""

        self._statusbar.set_score(self._game.get_score())

        # Increase the lights if score increment is greater than 12
        if self._game.get_score() - self._prev_score > 12:
            self._lights += 1
            self._lightning.config(text='Lightning OFF ({})'.format(self._lights), state=tk.NORMAL)
        self._prev_score = self._game.get_score()

    def lightning_effect(self):
        """
        Handles the lightning button effect
        """
        if self._lights >= 1:
            self._light_toggle = not self._light_toggle
            if self._light_toggle:
                self._lightning.config(text='*** Striking ***'.format(self._lights))
            else:
                self._lightning.config(text='Lightning OFF ({})'.format(self._lights))
        else:
            self._lightning.config(state=tk.DISABLED, text='No lights avalilable')
            self._light_toggle = not self._light_toggle

    def game_over(self):
        """
        Handles Game Over dialogue box
        """
        if self._game.get_name() == 'Objective':
            pass
        elif self._lights > 0:
            return
        sound = pygame.mixer.Sound("gameover.ogg")
        pygame.mixer.Sound.play(sound)

        # records highscore

        self._high_scores.record(self._game.get_score(), self._game, self._player_name)

        # messagebox asking to play again or exit
        if messagebox.askyesno("Game Over", "Gmae Over. Your Score is {}. "
                                            "Do you want to restart the game?".format(self._game.get_score())):
            self.reset()
        else:
            self._master.quit()


    def reset(self):
        """Resets the game."""

        self._game.set_score(0)
        self._game.reset()
        self._grid_view.draw(self._game.grid, self._game.find_connections())

    def exit(self):
        """
        Quits the application
        """
        self._parent_frame.quit()

class LoloApp2(tk.Frame):
    """
    Loading class for Lolo Game --> Inherit from tk.Frame
    """
    def __init__(self, master):
        """Constructor

        Parameters:
            master (tk.Tk|tk.Frame): The parent widget.

        """
        self._parent_frame = master

        # Initialize top bar frame and pack it
        self._top_bar = tk.Frame(self._parent_frame)
        self._top_bar.pack()

        # Initialize left bar frame and pack it
        self._left_bar = tk.Frame(self._parent_frame)
        self._left_bar.pack(side=tk.LEFT, padx=50, expand=True)

        # Right bar frame
        self._right_bar = tk.Frame(self._parent_frame)
        self._right_bar.pack(side=tk.RIGHT, padx=20, pady=10, expand=True)

        # Initialize the Logo Canvas and pack it
        self._logo = LoloLogo(self._top_bar, width=400, height=100)
        self._logo.pack(side=tk.TOP, expand=True, anchor=tk.CENTER)


        # Dictionary to store game modes
        self._game_modes = {'Regular Game': game_regular.RegularGame(), 'Make13': game_make13.Make13Game(),
                            'Lucky7': game_lucky7.Lucky7Game(), 'Unlimited': game_unlimited.UnlimitedGame(),
                            'Objective': game_objective.ObjectiveGame()}

        self._game_modes_play = {'Regular Game': game_regular.RegularGame(), 'Make13': game_make13.Make13Game(),
                            'Lucky7': game_lucky7.Lucky7Game(), 'Unlimited': game_unlimited.UnlimitedGame(),
                                 'Objective': game_objective.ObjectiveGame()}

        self._selected_game = game_regular.RegularGame()
        self._selected_game_play = game_regular.RegularGame()

        # Initialize the menubar and pass the arguments
        self.menubar = tk.Menu(master)
        menu = tk.Menu(self.menubar, tearoff=0)
        self.menubar.add_cascade(label="File", menu=menu)
        menu.add_command(label="Exit", command=self.exit)
        master.config(menu=self.menubar)

        # Display game mode on title bar of the window
        master.title('Lolo Game Main Screen')

        # High score class instance
        self._high_scores = highscores.HighScoreManager(gamemode=self._selected_game.get_name().lower())

        # generate all buttons and main UI
        self.all_buttons()

        pygame.init()
        icon = pygame.image.load('logo.jpg')
        pygame.display.set_icon(icon)

        pygame.mixer.music.load('background.mp3')
        pygame.mixer.music.play(-1)

    def all_buttons(self):
        """
        Initialize and pack all the widgets here to avoid cluttering in constructor.
        """

        # Name Label
        self._your_name = tk.Label(self._top_bar, text='Enter your name')
        self._your_name.pack()

        # Name Field
        self._name_field = tk.Entry(self._top_bar)
        self._name_field.pack()

        # Play Game button
        self._play_game = tk.Button(self._left_bar, text='New Game', width=20, command=self.play_game)
        self._play_game.pack(pady=20)

        # Load game button
        self._load_game = tk.Button(self._left_bar, text='Load Game', width=20, command=self.load_games)
        self._load_game.pack(anchor=tk.S, pady=10)

        # Game Mode button
        self._game_mode = tk.Button(self._left_bar, text='Select Game Mode', width=20, command=self.game_mode_window)
        self._game_mode.pack(pady=20)

        # High score button
        self._high_socre = tk.Button(self._left_bar, text='High Score', width=20,
                                     command=self.high_scores_display)
        self._high_socre.pack(pady=20)

        # Exit button
        self._exit = tk.Button(self._left_bar, text='Exit', width=20, command=self.exit)
        self._exit.pack(pady=20)

        # Visual representation of autoplaying game
        self._game_repr = AutoPlayingGame(self._right_bar)

        self._volume_control = tk.Scale(self._left_bar, from_=0, to_=1, orient=tk.HORIZONTAL, resolution=.1,
                                        length=200,
                                        command=lambda x: pygame.mixer.music.set_volume(self._volume_control.get()))
        self._volume_control.pack(side=tk.BOTTOM, pady=20)
        self._volume_control.set(.5)

        # music toggle buttons
        self._music_on = tk.Button(self._left_bar, text='Music ON', width=10,
                                       command=lambda: pygame.mixer.music.play(-1))
        self._music_on.pack(side=tk.LEFT, pady=20)

        self._music_off = tk.Button(self._left_bar, text='Music OFF', width=10,
                                       command=lambda: pygame.mixer.music.stop())
        self._music_off.pack(side=tk.RIGHT, pady=20)

    def load_games(self):
        """
        Initialize saved games manager instance and get the data for the selected game

        Return:
            names_list(list): List of names of the selected saved game mode from file
        """
        # Saved games instance
        saved_games = save_game.SaveLoadManager(gamemode=self._selected_game.get_name().lower())
        self.data = saved_games.get_sorted_data()
        names_list = [i.get('name') for i in self.data]

        self._selected_player = []

        top = tk.Toplevel(self._parent_frame)

        games_list = tk.Listbox(top, width=50, height=20)
        games_list.pack(fill=tk.BOTH, expand=True)

        for i in names_list:
            games_list.insert(tk.END, i)

        seletction = tk.Button(top, text='Play this game',
                               command=lambda: self.play_loaded_game(games_list.curselection()))
        seletction.pack()


    def play_loaded_game(self, player):
        """
        Plays the loaded game
        """
        print(player)
        return
        data = next(i for i in self.data if i.get('name') ==  self._load_var.get())
        grid_list = data.get('grid')
        game = self._selected_game_play.deserialize(grid_list)

        # Initialize a Toplevel window for gameplay
        top = tk.Toplevel(self._parent_frame)

        grid_view = view.GridView(top, game.grid.size())

        play_game = LoloApp(top, game=self._selected_game_play, player_name=data.get('name'),
                            grid_view=grid_view, default_score=data.get('score'))


    def play_game(self):
        """
        Handles start of gameplay button
        """
        # warning when trying to start the game without giving a name
        if self._name_field.get() == "":
            return messagebox.showwarning("Name Missing", "Please provide your name first")

        # Initialize a Toplevel window for gameplay
        top = tk.Toplevel(self._parent_frame)
        game = LoloApp(top, self._selected_game_play, self._name_field.get())

        # Hiding the loading screen for undistracted gameplay
        self._parent_frame.withdraw()

        def override_x():
            """
            Overriding the close button for Toplevel window
             This will get the loading screen to reappear
            """
            top.destroy()
            self._parent_frame.destroy()

        top.protocol("WM_DELETE_WINDOW", override_x)

    def autoplay_repr(self):
        """
        Autoplay representation on the loading screen
        """

        self._selected_game = self._game_modes.get(self._game_mode_var.get())
        self._selected_game_play = self._game_modes_play.get(self._game_mode_var.get())
        # first destroy the frame
        self._right_bar.destroy()
        # redraw Right bar frame
        self._right_bar = tk.Frame(self._parent_frame)
        self._right_bar.pack(side=tk.RIGHT, padx=20, pady=20, expand=True)

        self._game_repr = AutoPlayingGame(self._right_bar, self._selected_game)


    def high_scores_display(self):
        """
        Displays high score / leaderboard in a Toplevel
        """

        top = tk.Toplevel(self._parent_frame)
        top.title('Leaderboard')

        # Leaderboard Frames
        self._best_player_frame = tk.Frame(top)
        self._best_player_frame.pack(expand=True, pady=5, padx=10)

        # Best player label
        self._best_player = self._high_scores.get_sorted_data()[0]
        self._best_player_label = tk.Label(self._best_player_frame,
                                           text='Best Player: {} with {} points!'.format(self._best_player.get('name'),
                                                                                         self._best_player.get('score')))
        self._best_player_label.pack()

        # Best player static visual representation
        grid_list = self._best_player.get('grid')
        game = game_regular.RegularGame.deserialize(grid_list)
        grid_view = view.GridView(self._best_player_frame, game.grid.size())
        self._grid_view = grid_view
        self._grid_view.pack()

        self._grid_view.draw(game.grid, game.find_connections())

        # Leaderboard score table
        score_frame = tk.Frame(top)
        score_frame.pack(pady=5, padx=20)

        rows = 0
        for i in self._high_scores.get_sorted_data():
            name_label = tk.Label(score_frame, text=i.get('name')).grid(row=rows, column=0, sticky='nw', padx=20)
            score_label = tk.Label(score_frame, text=i.get('score')).grid(row=rows, column=1, sticky='ne', padx=20)
            rows += 1

    def game_mode_window(self):
        """
        Dsiplays game modes selection in a Toplevel
        """

        # warning when trying to start the game without giving a name
        if self._name_field.get() == "":
            return messagebox.showwarning("Name Missing", "Please provide your name first")

        top = tk.Toplevel(self._parent_frame)
        top.title('Select Game Mode')

        game_mode_frame = tk.Frame(top)
        game_mode_frame.pack(side=tk.LEFT, padx=50, pady=50)

        # game mode selection options using radiobuttons

        self._select_game_label = tk.Label(game_mode_frame, text='Select game mode to play')
        self._select_game_label.pack(anchor='center', padx=10, pady=10)

        self._game_mode_var = tk.StringVar(game_mode_frame)
        self._game_mode_var.set('Regular Game')

        self._option1 = tk.Radiobutton(game_mode_frame, text='Regular', variable=self._game_mode_var, value='Regular Game',
                                       command=self.autoplay_repr).pack(anchor='nw', padx=10, pady=10)
        self._option2 = tk.Radiobutton(game_mode_frame, text='Make13', variable=self._game_mode_var, value='Make13',
                                       command=self.autoplay_repr).pack(anchor='nw', padx=10, pady=10)
        self._option3 = tk.Radiobutton(game_mode_frame, text='lucky7', variable=self._game_mode_var, value='Lucky7',
                                       command=self.autoplay_repr).pack(anchor='nw', padx=10, pady=10)
        self._option4 = tk.Radiobutton(game_mode_frame, text='Unlimited', variable=self._game_mode_var, value='Unlimited',
                                       command=self.autoplay_repr).pack(anchor='nw', padx=10, pady=10)
        self._option5 = tk.Radiobutton(game_mode_frame, text='Objective', variable=self._game_mode_var,
                                       value='Objective',
                                       command=self.autoplay_repr).pack(anchor='nw', padx=10, pady=10)

    def exit(self):
        """
        Quits the application
        """
        self._parent_frame.quit()

class LoloLogo(tk.Canvas):
    """
    LoloLogo class for drawing logo from canvas shapes
    """
    def __init__(self, master, **kwargs):
        """
        Constructor method for drawing Logo on canvas

        Parameters:
            master (tk.Frame): The parent widget
            **kwargs (parameters): Key arguments for canvas dimensions and behavior
        """
        super().__init__(master, **kwargs)

        # First L
        self.create_rectangle(20, 10, 50, 100, fill='#f1727f', width=0)
        self.create_rectangle(20, 70, 100, 100, fill='#f1727f', width=0)

        # First O
        self.create_oval(120, 30, 180, 90, fill='white', outline='#78aecc', width=20)

        # Second L
        self.create_rectangle(200, 10, 230, 100, fill='#ffcc70', width=0)
        self.create_rectangle(200, 70, 290, 100, fill='#ffcc70', width=0)

        # Second O
        self.create_oval(310, 30, 370, 90, fill='white', outline='#4c6177', width=20)

class StatusBar(tk.Frame):
    """
    Statusbar for Lolo App Game Screen
    """

    def __init__(self, master):
        """
        Constructor method for Statusbar

         Parameters:
             master (tk.Frame): The parent widget
        """
        super().__init__(master)

        # Score Label
        self._score = tk.Label(self, text="Score: 0")
        self._score.pack(side=tk.RIGHT, padx=10)

        # Game Label
        self._game_label = tk.Label(self, text="")
        self._game_label.pack(side=tk.LEFT, padx=10)

    def set_game(self, game_mode):
        """
        Display current game mode

         Parameters:
             game_mode (object): A game object
        """
        self._game_label.config(text=game_mode.get_name()+' Game')

    def set_score(self, score):
        """
        Display current score of the user

         Parameters:
             score (int)
        """
        self._score.config(text="Score: {}".format(score))

class AutoPlayingGame(BaseLoloApp):
    """
    Auto playing game class
    """
    def __init__(self, master, game=None, grid_view=None):

        super().__init__(master, game, grid_view)

        master.after(200, self.autoplay)

    def bind_events(self):
        """Override bind_event of parent class."""
        self._grid_view.off('select', self.activate)
        self._game.on('game_over', self.game_over)
        self._game.on('score', self.score)

    def autoplay(self):
        """
        Randomly finds a valid tile and activates it
        """

        try:
            object = next(self._game.find_groups())
        except:
            return

        try:
            self.activate(random.sample(object, 1)[0])
            self._master.after(2000, self.autoplay)
        except:
            self.autoplay()

    def score(self, score):
        """ Overrrides the score method to keep it quiet"""
        return

    def game_over(self):
        """
        Overrides the gameover method to replay the game continously
        """

        self._game.reset()
        self._grid_view.draw(self._game.grid, self._game.find_connections())


def main():
    root = tk.Tk()
    app = LoloApp2(root)
    # app = AutoPlayingGame(root)
    root.mainloop()


if __name__ == "__main__":
    main()
