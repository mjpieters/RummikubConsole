from set_generator import SetGenerator
from solver import RummikubSolver


def console_qa(q, *conditions):
    while True:
        print(q)
        inp = input()
        a = inp.lower() if inp.lower() in [str(c) for c in conditions] else None
        if a is not None:
            return a
        else:
            print('Invalid input')


def create_number_maps(sg):
    colours = ['bk', 'bl', 'or', 'rd']
    verbose_list = [f'{colours[c]}{n}' for c in range(sg.colours) for n in range(1, sg.numbers + 1)]
    verbose_list.append('j')
    tile_map = dict(zip(verbose_list, sg.tiles))
    r_tile_map = {v: k for k, v in tile_map.items()}
    return tile_map, r_tile_map


def print_solution(solver, r_tile_map):
    value, tiles, sets = solver.solve()
    if value == 0:
        print('No solution found - pick up.')
    else:
        tile_list = [solver.tiles[i] for i in range(len(tiles)) if tiles[i] == 1]
        set_list = [solver.sets[i] for i in range(len(sets)) if sets[i] == 1]
        print(f"Using the following tiles from your rack: {', '.join([r_tile_map[t] for t in tile_list])}")
        print('Make the following sets:')
        for s in set_list:
            print(f"{', '.join([r_tile_map[t] for t in s])}")
        auto_add_remove = console_qa('Automatically place tiles for selected solution? [Y/n]', '', 'y', 'n')
        if auto_add_remove == '' or auto_add_remove == 'Y':
            solver.remove_rack(tile_list)
            solver.add_table(tile_list)
            print('Placed tiles on table')


def main():
    default_rummikub = console_qa('Default rummikub rules? [Y/n]', '', 'y', 'n')
    if default_rummikub == '' or default_rummikub == 'Y':
        sg = SetGenerator()
    else:
        numbers = int(console_qa('Numbers? [1-26]', *list(range(1, 27))))
        colours = int(console_qa('Colours? [1-8]', *list(range(1, 9))))
        jokers = int(console_qa('Jokers? [0-4]', *list(range(1, 5))))
        min_len = int(console_qa('Minimum set length? [2-6]', *list(range(2, 7))))
        sg = SetGenerator(numbers=numbers, colours=colours, jokers=jokers, min_len=min_len)

    tile_map, r_tile_map = create_number_maps(sg)

    solver = RummikubSolver(tiles=sg.tiles, sets=sg.sets)

    print('Solver initiated...')

    while True:
        inp = input()
        command = inp.split(' ')[0]
        args = inp.split(' ')[1:]
        for arg in args:
            if arg not in [*tile_map.keys(), None]:
                print('Invalid input')
                continue
        if command == 'r':
            print(f"{', '.join(r_tile_map[t] for t in solver.rack)}")
        elif command == 't':
            print(f"{', '.join(r_tile_map[t] for t in solver.table)}")
        elif command == 'ar':
            solver.add_rack([tile_map[c] for c in args])
            print('Added tiles to rack')
        elif command == 'rr':
            solver.remove_rack([tile_map[c] for c in args])
            print('Removed tiles from rack')
        elif command == 'at':
            solver.add_table([tile_map[c] for c in args])
            print('Added tiles to table')
        elif command == 'rt':
            solver.remove_table([tile_map[c] for c in args])
            print('Removed tiles from table')
        elif command == 'solve':
            print_solution(solver, r_tile_map)
        elif command == 'stop' or command == 'end' or command == 'quit':
            break
        else:
            print('Invalid command')

    print('Thank you for playing!')


if __name__ == '__main__':
    main()
