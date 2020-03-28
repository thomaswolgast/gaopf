# util.py
""" Utility functions for the GeneticAlgo OPF for pandapower. """

import datetime
import os

import matplotlib.pyplot as plt
import pandapower as pp


def create_path():
    """ Create folder for data saving. The name of the folder is the
    current date and time. Attention: Time in virtualbox and time in host
    system are not always synchronous! """
    t = datetime.datetime.now().replace(microsecond=0).isoformat()
    path = f'OPF_Results/{t}/'.replace(':', '.').replace('T', ' ')
    os.makedirs(path)
    return path


def save_net(best_net, path: str, format_='pickle'):
    """ Save pandapower network to some format. """
    filename = 'best_net'
    if format_ == 'pickle':
        pp.to_pickle(best_net, path+filename+'.p')
    elif format_ == 'json':
        pp.to_json(best_net, path+filename+'.json')
    else:
        print(f'File format "{format_}" not implemented yet!')


def plot_fit_courses(save: bool, path: str,
                     best_fit_course=None, total_best_fit_course=None,
                     avrg_fit_course=None, format_type='png'):
    """ Plot the total best fitness value, the best fitness value of the
    respective step as course over the iterations. (Also possible: Plot the
    average fitness. Problematic because of penalties) """

    if best_fit_course:
        plt.plot(best_fit_course, label='Best costs')
    if total_best_fit_course:
        plt.plot(total_best_fit_course, label='Total best costs')
    if avrg_fit_course:
        plt.plot(avrg_fit_course, label='Average costs')

    plt.legend(loc='upper right')
    plt.ylabel('Total costs')
    plt.xlabel('Iteration number')

    if save is True:
        plt.savefig(f'{path}optimization_course.{format_type}',
                    format=format_type,
                    bbox_inches='tight')
        plt.close()
    else:
        plt.show()
