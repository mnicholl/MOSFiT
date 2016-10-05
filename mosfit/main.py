import argparse
import os
import shutil
from textwrap import wrap

from emcee.utils import MPIPool
from mosfit.fitter import Fitter

from mosfit import __version__


def main():
    """First, parse command line arguments.
    """

    dir_path = os.path.dirname(os.path.realpath(__file__))

    parser = argparse.ArgumentParser(
        prog='MOSFiT',
        description='Fit astrophysical light curves using AstroCats data.')

    parser.add_argument(
        '--events',
        '-e',
        dest='events',
        default=[''],
        nargs='+',
        help=("List of event names to be fit, delimited by spaces. If an "
              "event name contains a space, enclose the event's name in "
              "double quote marks, e.g. \"SDSS-II SN 5944\"."))

    parser.add_argument(
        '--models',
        '-m',
        dest='models',
        default=['default'],
        nargs='+',
        help=("List of models to use to fit against the listed events. The "
              "model can either be a name of a model included with MOSFiT, or "
              "a path to a custom model JSON file generated by the user."))

    parser.add_argument(
        '--parameter-paths',
        '-P',
        dest='parameter_paths',
        default=[''],
        nargs='+',
        help=("Paths to parameter files corresponding to each model file; "
              "length of this list should be equal to the length of the list "
              "of models"))

    parser.add_argument(
        '--plot-points',
        dest='plot_points',
        default=100,
        help=("Set the number of plot points when producing light curves from "
              "models without fitting against any actual transient data."))

    parser.add_argument(
        '--max-time',
        dest='max_time',
        type=float,
        default=1000.,
        help=("Set the maximum time for model light curves to be plotted "
              "until."))

    parser.add_argument(
        '--band-list',
        dest='band_list',
        default=['V'],
        nargs='+',
        help=("List of bands to plot when plotting model light curves that "
              "are not being matched to actual transient data."))

    parser.add_argument(
        '--band-systems',
        dest='band_systems',
        default=[],
        nargs='+',
        help=("List of photometric systems corresponding to the bands listed "
              "in `--band-list`."))

    parser.add_argument(
        '--band-instruments',
        dest='band_instruments',
        default=[],
        nargs='+',
        help=("List of instruments corresponding to the bands listed "
              "in `--band-list`."))

    parser.add_argument(
        '--iterations',
        '-i',
        dest='iterations',
        type=int,
        default=-1,
        help=("Number of iterations to run emcee for, including burn-in and "
              "post-burn iterations."))

    parser.add_argument(
        '--num-walkers',
        '-N',
        dest='num_walkers',
        type=int,
        default=50,
        help=("Number of walkers to use in emcee, must be at least twice the "
              "total number of free parameters within the model."))

    parser.add_argument(
        '--num-temps',
        '-T',
        dest='num_temps',
        type=int,
        default=2,
        help=("Number of temperatures to use in the parallel-tempered emcee "
              "sampler. `-T 1` is equivalent to the standard "
              "EnsembleSampler."))

    parser.add_argument(
        '--no-fracking',
        dest='fracking',
        default=True,
        action='store_false',
        help=("Setting this flag will skip the `fracking` step of the "
              "optimization process."))

    parser.add_argument(
        '--no-copy-at-launch',
        dest='copy',
        default=True,
        action='store_false',
        help=("Setting this flag will prevent MOSFiT from copying the user "
              "file hierarchy (models/modules/jupyter) to the current working "
              "directory before fitting."))

    parser.add_argument(
        '--force-copy-at-launch',
        dest='force_copy',
        default=False,
        action='store_true',
        help=("Setting this flag will force MOSFiT to overwrite the user "
              "file hierarchy (models/modules/jupyter) to the current working "
              "directory. User will be prompted before being allowed to run "
              "with this flag."))

    parser.add_argument(
        '--frack-step',
        '-f',
        dest='frack_step',
        type=int,
        default=20,
        help=("Perform `fracking` every this number of steps while in the "
              "burn-in phase of the fitting process."))

    parser.add_argument(
        '--post-burn',
        '-p',
        dest='post_burn',
        type=int,
        default=500,
        help=("Run emcee this many more iterations after the burn-in phase. "
              "The burn-in phase will thus be run for (i - p) iterations, "
              "where i is the total number of iterations set with `-i` and "
              "p is the value of this parameter."))

    parser.add_argument(
        '--travis',
        dest='travis',
        default=False,
        action='store_true',
        help=("Alters the printing of output messages such that a new line is "
              "generated with each message. Users are unlikely to need this "
              "parameter; it is included as Travis requires new lines to be "
              "produed to detected program output."))

    args = parser.parse_args()

    changed_iterations = False
    if args.iterations == -1:
        if len(args.events) == 1 and args.events[0] == '':
            changed_iterations = True
            args.iterations = 0
        else:
            args.iterations = 1000

    pool = ''
    try:
        pool = MPIPool(loadbalance=True)
    except ValueError:
        pass
    except:
        raise

    width = 100
    if not pool or pool.is_master():
        # Print our amazing ASCII logo.
        with open(os.path.join(dir_path, 'logo.txt'), 'r') as f:
            logo = f.read()
            width = len(logo.split('\n')[0])
            aligns = '{:^' + str(width) + '}'
            print(logo)
        print((aligns + '\n').format('### MOSFiT -- version {} ###'.format(
            __version__)))
        print(aligns.format('Authored by James Guillochon & Matt Nicholl'))
        print(aligns.format('Released under the MIT license'))
        print((aligns + '\n').format('https://github.com/guillochon/MOSFiT'))

        if changed_iterations:
            print("\n\nNo events specified, setting iterations to 0.")

        # Create the user directory structure, if it doesn't already exist.
        if args.copy:
            print(
                'Copying MOSFiT folder hierarchy to current working directory '
                '(disable with --no-copy-at-launch).')
            fc = False
            if args.force_copy:
                prompt_txt = wrap(
                    "The flag `--force-copy-at-launch` has been set. Do you "
                    "really wish to overwrite your local model/module/jupyter "
                    "file hierarchy? This action cannot be reversed. "
                    "[Y/(N)]: ", width)
                for txt in prompt_txt[:-1]:
                    print(txt)
                user_choice = input(prompt_txt[-1] + " ")
                fc = user_choice in ["Y", "y", "Yes", "yes"]
            if not os.path.exists('jupyter'):
                os.mkdir(os.path.join('jupyter'))
            if not os.path.isfile(os.path.join('jupyter',
                                               'mosfit.ipynb')) or fc:
                shutil.copy(
                    os.path.join(dir_path, 'jupyter', 'mosfit.ipynb'),
                    os.path.join(os.getcwd(), 'jupyter', 'mosfit.ipynb'))

            # Disabled for now as external modules don't work with MPI.
            # if not os.path.exists('modules'):
            #     os.mkdir(os.path.join('modules'))
            # module_dirs = next(os.walk(os.path.join(dir_path, 'modules')))[1]
            # for mdir in module_dirs:
            #     if mdir.startswith('__'):
            #         continue
            #     mdir_path = os.path.join('modules', mdir)
            #     if not os.path.exists(mdir_path):
            #         os.mkdir(mdir_path)

            if not os.path.exists('models'):
                os.mkdir(os.path.join('models'))
            model_dirs = next(os.walk(os.path.join(dir_path, 'models')))[1]
            for mdir in model_dirs:
                if mdir.startswith('__'):
                    continue
                mdir_path = os.path.join('models', mdir)
                if not os.path.exists(mdir_path):
                    os.mkdir(mdir_path)
                model_files = next(
                    os.walk(os.path.join(dir_path, 'models', mdir)))[2]
                for mfil in model_files:
                    fil_path = os.path.join(os.getcwd(), 'models', mdir, mfil)
                    if os.path.isfile(fil_path) and not fc:
                        continue
                    shutil.copy(
                        os.path.join(dir_path, 'models', mdir, mfil),
                        os.path.join(fil_path))
    else:
        pool.wait()

    if pool:
        pool.close()

    # Then, fit the listed events with the listed models.
    fitargs = {
        'events': args.events,
        'models': args.models,
        'plot_points': args.plot_points,
        'max_time': args.max_time,
        'band_list': args.band_list,
        'band_systems': args.band_systems,
        'band_instruments': args.band_instruments,
        'iterations': args.iterations,
        'num_walkers': args.num_walkers,
        'num_temps': args.num_temps,
        'parameter_paths': args.parameter_paths,
        'fracking': args.fracking,
        'frack_step': args.frack_step,
        'wrap_length': width,
        'travis': args.travis,
        'post_burn': args.post_burn
    }
    Fitter().fit_events(**fitargs)


if __name__ == "__main__":
    main()
