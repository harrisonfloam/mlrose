"""Functions to implement the randomized optimization and search algorithms."""

# Authors: Genevieve Hayes (modified by Andrew Rollings, Kyle Nakamura)
# License: BSD 3-clause

import numpy as np
from typing import Callable, Any
from mlrose_ky.decorators import short_name


@short_name("rhc")
def random_hill_climb(
    problem: Any,
    max_attempts: int = 10,
    max_iters: int = np.inf,
    restarts: int = 0,
    init_state: np.ndarray = None,
    curve: bool = False,
    random_state: int = None,
    state_fitness_callback: Callable = None,
    callback_user_info: Any = None,
) -> tuple[np.ndarray, float, np.ndarray | None]:
    """Use randomized hill climbing to find the optimum for a given optimization problem.

    Parameters
    ----------
    problem: optimization object
        Object containing fitness function optimization problem to be solved.
        For example, :code:`DiscreteOpt()`, :code:`ContinuousOpt()` or
        :code:`TSPOpt()`.
    max_attempts: int, default: 10
        Maximum number of attempts to find a better neighbor at each step.
    max_iters: int, default: np.inf
        Maximum number of iterations of the algorithm.
    restarts: int, default: 0
        Number of random restarts.
    init_state: np.ndarray, default: None
        1-D Numpy array containing starting state for algorithm.
        If :code:`None`, then a random state is used.
    curve: bool, default: False
        Boolean to keep fitness values for a curve.
        If :code:`False`, then no curve is stored.
        If :code:`True`, then a history of fitness values is provided as a
        third return value.
    random_state: int, default: None
        If random_state is a positive integer, random_state is the seed used
        by np.random.seed(); otherwise, the random seed is not set.
    state_fitness_callback: function taking five parameters, default: None
        If specified, this callback will be invoked once per iteration.
        Parameters are (iteration, max attempts reached?, current best state, current best fit, user callback data).
        Return true to continue iterating, or false to stop.
    callback_user_info: any, default: None
        User data passed as last parameter of callback.

    Returns
    -------
    best_state: np.ndarray
        Numpy array containing state that optimizes the fitness function.
    best_fitness: float
        Value of fitness function at best state.
    fitness_curve: np.ndarray
        Numpy array containing the fitness at every iteration.
        Only returned if input argument :code:`curve` is :code:`True`.

    References
    ----------
    Brownlee, J (2011). *Clever Algorithms: Nature-Inspired Programming Recipes*.
    `<http://www.cleveralgorithms.com>`_.
    """
    # if not isinstance(max_attempts, int) or max_attempts < 0:
    #     raise ValueError(f"max_attempts must be a positive integer. Got {max_attempts}")
    # if not (isinstance(max_iters, int) or max_iters == np.inf) or max_iters < 0:
    #     raise ValueError(f"max_iters must be a positive integer or np.inf. Got {max_iters}")
    # if not isinstance(restarts, int) or restarts < 0:
    #     raise ValueError(f"restarts must be a positive integer. Got {restarts}")
    # if init_state is not None and len(init_state) != problem.get_length():
    #     raise ValueError(
    #         f"init_state must have the same length as the problem. Expected length {problem.get_length()}, got {len(init_state)}"
    #     )

    # Set random seed
    if isinstance(random_state, int) and random_state > 0:
        np.random.seed(random_state)

    best_fitness = -np.inf
    best_state = None
    best_fitness_curve = []
    all_curves = []

    for current_restart in range(restarts + 1):
        # Initialize problem
        fitness_curve = []
        fevals = problem.fitness_evaluations
        if init_state is None:
            problem.reset()
        else:
            problem.set_state(init_state)

        problem.fitness_evaluations = fevals

        callback_extra_data = None
        if state_fitness_callback is not None:
            callback_extra_data = callback_user_info + [("current_restart", current_restart)]
            # initial call with base data
            state_fitness_callback(
                iteration=0,
                state=problem.get_state(),
                fitness=problem.get_adjusted_fitness(),
                fitness_evaluations=problem.fitness_evaluations,
                user_data=callback_extra_data,
            )

        attempts = 0
        iters = 0
        while attempts < max_attempts and iters < max_iters:
            iters += 1
            problem.current_iteration += 1

            # Find random neighbor and evaluate fitness
            next_state = problem.random_neighbor()
            next_fitness = problem.eval_fitness(next_state)

            # FIXME: RHC should move to neighbor if >= current fitness (?)
            # If best neighbor is an improvement, move to that state and reset attempts counter
            current_fitness = problem.get_fitness()
            if next_fitness > current_fitness:
                problem.set_state(next_state)
                attempts = 0
            else:
                attempts += 1

            if curve:
                adjusted_fitness = problem.get_adjusted_fitness()
                curve_value = (adjusted_fitness, problem.fitness_evaluations)
                fitness_curve.append(curve_value)
                all_curves.append(curve_value)

            # invoke callback
            if state_fitness_callback is not None:
                max_attempts_reached = (attempts == max_attempts) or (iters == max_iters) or problem.can_stop()
                continue_iterating = state_fitness_callback(
                    iteration=iters,
                    attempt=attempts + 1,
                    done=max_attempts_reached,
                    state=problem.get_state(),
                    fitness=problem.get_adjusted_fitness(),
                    fitness_evaluations=problem.fitness_evaluations,
                    curve=np.asarray(all_curves) if curve else None,
                    user_data=callback_extra_data,
                )
                # break out if requested
                if not continue_iterating:
                    break

        # Update best state and best fitness
        current_fitness = problem.get_fitness()
        if current_fitness > best_fitness:
            best_fitness = current_fitness
            best_state = problem.get_state()
            if curve:
                best_fitness_curve = [*fitness_curve]

        # break out if we can stop
        if problem.can_stop():
            break

    best_fitness *= problem.get_maximize()

    if curve:
        return best_state, best_fitness, np.asarray(best_fitness_curve)

    return best_state, best_fitness, None
