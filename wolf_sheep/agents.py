import mesa

from .random_walk import RandomWalker


class Sheep(RandomWalker):
    """
    A sheep that walks around, reproduces (asexually) and gets eaten.

    The init is the same as the RandomWalker.
    """

    energy = None

    def __init__(self, unique_id, model, moore, energy=None):
        super().__init__(unique_id, model, moore=moore)
        self.energy = energy


    def step(self):
        """
        A model step. Move, then eat grass and reproduce.
        """
        self.random_move()
        living = True

        # Рандомізація швидкості переміщення
        speed_factor = self.random.random() * 2  # швидкість між 0 і 2
        for _ in range(int(speed_factor)):
            self.random_move()

        if self.model.grass:
            # Reduce energy
            self.energy -= 1

            # If there is grass available, eat it
            this_cell = self.model.grid.get_cell_list_contents([self.pos])
            grass_patch = next(obj for obj in this_cell if isinstance(obj, GrassPatch))
            if grass_patch.fully_grown:
                self.energy += self.model.sheep_gain_from_food
                grass_patch.fully_grown = False

            # Death
            if self.energy < 0:
                self.model.grid.remove_agent(self)
                self.model.schedule.remove(self)
                living = False

        if living and self.random.random() < self.model.sheep_reproduce:
            # Create a new sheep:
            if self.model.grass:
                self.energy /= 2
            lamb = Sheep(self.model.next_id(), self.model, self.moore, self.energy)
            self.model.grid.place_agent(lamb, self.pos)
            self.model.schedule.add(lamb)


class Wolf(RandomWalker):
    """
    A wolf that walks around, reproduces (asexually) and eats sheep.
    """

    energy = None

    def __init__(self, unique_id, model, moore, energy=None):
        super().__init__(unique_id, model, moore=moore)
        self.energy = energy


    def step(self):
        self.random_move()
        self.energy -= 1

        # Рандомізація швидкості переміщення
        speed_factor = self.random.random() * 2  # швидкість між 0 і 2
        for _ in range(int(speed_factor)):
            self.random_move()
        # If there are sheep present, eat one
        x, y = self.pos
        this_cell = self.model.grid.get_cell_list_contents([self.pos])
        sheep = [obj for obj in this_cell if isinstance(obj, Sheep)]
        if len(sheep) > 0:
            sheep_to_eat = self.random.choice(sheep)
            self.energy += self.model.wolf_gain_from_food

            # Kill the sheep
            self.model.grid.remove_agent(sheep_to_eat)
            self.model.schedule.remove(sheep_to_eat)

        # Death or reproduction
        if self.energy < 0:
            self.model.grid.remove_agent(self)
            self.model.schedule.remove(self)
        else:
            if self.random.random() < self.model.wolf_reproduce:
                # Create a new wolf cub
                self.energy /= 2
                cub = Wolf(self.model.next_id(), self.model, self.moore, self.energy)
                self.model.grid.place_agent(cub, self.pos)
                self.model.schedule.add(cub)


class GrassPatch(mesa.Agent):
    """
    A patch of grass that grows at a fixed rate and it is eaten by sheep
    """

    def __init__(self, unique_id, model, fully_grown, countdown):
        """
        Creates a new patch of grass

        Args:
            grown: (boolean) Whether the patch of grass is fully grown or not
            countdown: Time for the patch of grass to be fully grown again
        """
        super().__init__(unique_id, model)
        self.fully_grown = fully_grown
        self.countdown = countdown
        self.grow_timer = 0


    def step(self):
        sheep_count = sum(
            1 for agent in self.model.grid.get_neighbors(self.pos, moore=True) if isinstance(agent, Sheep))

        if not self.fully_grown:
            # Чим більше овець поруч, тим повільніше росте трава
            growth_rate = 3 + sheep_count
            self.grow_timer += growth_rate
            if self.grow_timer >= 15:
                self.fully_grown = True
                self.grow_timer = 0

        if not self.fully_grown:
            if self.countdown <= 0:
                # Set as fully grown
                self.fully_grown = True
                self.countdown = self.model.grass_regrowth_time
            else:
                self.countdown -= 1
