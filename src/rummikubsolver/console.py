from .set_generator import SetGenerator
from .solver import RummikubSolver


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
    colours = ['k', 'b', 'o', 'r']
    verbose_list = [f'{colours[c]}{n}' for c in range(sg.colours) for n in range(1, sg.numbers + 1)]
    verbose_list.append('j')
    tile_map = dict(zip(verbose_list, sg.tiles))
    r_tile_map = {v: k for k, v in tile_map.items()}
    return tile_map, r_tile_map


def print_solution(solver, r_tile_map, maximise='tiles', initial_meld=False):
    value, tiles, sets = solver.solve(maximise=maximise, initial_meld=initial_meld)
    if value == 0 or (initial_meld and value < 30):
        print('No solution found - pick up.')
    else:
        tile_list = [solver.tiles[i] for i in range(len(tiles)) if tiles[i] == 1]
        set_list = [solver.sets[i] for i in range(len(sets)) if sets[i] == 1]
        print(f"Using the following tiles from your rack:\n{', '.join([r_tile_map[t] for t in tile_list])}")
        print('Make the following sets:')
        for s in set_list:
            print(f"{', '.join([r_tile_map[t] for t in s])}")
        auto_add_remove = console_qa('Automatically place tiles for selected solution? [Y/n]', '', 'y', 'n')
        if auto_add_remove == '' or auto_add_remove == 'Y':
            solver.remove_rack(tile_list)
            solver.add_table(tile_list)
            print('Placed tiles on table')


def get_tile_count(tiles, r_tile_map):
    tiles_list = [r_tile_map[t] for t in tiles]
    colours = set([t[0] for t in tiles_list])
    colour_count = {
        c: len([0 for t in tiles_list if t[0] == c])
        for c in colours
    }
    return len(tiles_list), colour_count


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

    print('Running...')

    while True:
        inp = input()
        command = inp.split(' ')[0]
        args = inp.split(' ')[1:]
        for arg in args:
            if arg not in [*tile_map.keys(), None, 'tiles', 'value', 'initial']:
                print(f"Invalid argument: '{arg}'")
                args[:] = [a for a in args if a != arg]
        if command == 'r':
            print(f"{', '.join(r_tile_map[t] for t in solver.rack)}")
            rack_count, rack_c_count = get_tile_count(solver.rack, r_tile_map)
            print(f"{rack_count} tiles on rack: {', '.join([f'{ct}{c}' for c, ct in rack_c_count.items()])}")
        elif command == 't':
            print(f"{', '.join(r_tile_map[t] for t in solver.table)}")
            table_count, table_c_count = get_tile_count(solver.table, r_tile_map)
            print(f"{table_count} tiles on table: {', '.join([f'{ct}{c}' for c, ct in table_c_count.items()])}")
        elif command == 'ar':
            if len(args) > 0:
                solver.add_rack([tile_map[c] for c in args if c])
                print('Added tiles to rack')
        elif command == 'rr':
            if len(args) > 0:
                solver.remove_rack([tile_map[c] for c in args if c])
                print('Removed tiles from rack')
        elif command == 'at':
            if len(args) > 0:
                solver.add_table([tile_map[c] for c in args if c])
                print('Added tiles to table')
        elif command == 'rt':
            if len(args) > 0:
                solver.remove_table([tile_map[c] for c in args if c])
                print('Removed tiles from table')
        elif command == 'r2t':
            if len(args) > 0:
                solver.remove_rack([tile_map[c] for c in args if c])
                solver.add_table([tile_map[c] for c in args if c])
                print('Placed tiles from rack on table')
        elif command == 't2r':
            if len(args) > 0:
                solver.remove_table([tile_map[c] for c in args if c])
                solver.add_rack([tile_map[c] for c in args if c])
                print('Taken tiles from table and placed on rack')
        elif command == 'solve':
            if len(args) > 0:
                if args[0] == 'tiles':
                    print_solution(solver, r_tile_map, maximise='tiles')
                elif args[0] == 'value':
                    print_solution(solver, r_tile_map, maximise='value')
                elif args[0] == 'initial':
                    print_solution(solver, r_tile_map, maximise='value', initial_meld=True)
            else:
                print_solution(solver, r_tile_map)
        elif command == 'stop' or command == 'end' or command == 'quit':
            break
        else:
            print('Invalid command')

    print('Thank you for playing!')


if __name__ == '__main__':
    main()
