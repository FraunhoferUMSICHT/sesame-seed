import matplotlib.pyplot as plt

from cycler import cycler

class Plotstyles: 
    '''
    This class is used to manage colours in Fraunhofer-Design
    :param background: list with background-colours
    :param b_ix: Index to deal with backgroound colours
    :param accent: list with accent colours
    :param a_ix: Index to deal with accent colours
    :param custom: list with custom colours 
    :param c_ix: Index to deal with custom colours 
    '''
    def __init__(self):
        self.background = ['#FFFFFF', '#000000', '#A6BBC8', '#F58220']
        self.b_ix = 0
        self.accent = ['#A6BBC8', '#179C7D', '#005B7F',  '#008598', '#39C1CD', '#B2D235']
        self.a_ix = 0
        self.custom = ['#A6BBC8', '#179C7D', '#005B7F',  '#F58220', '#337C99', '#669DB2', '#99BDCC', '#CCDEE5', '#E5EEF2', '#1C3F52', '#D3C7AE', '#008598', '#39C1CD', '#B2D235', '#FDB913', '#BB056', '#7C154D']
        self.c_ix = 0

    def get_background(self):
        '''Function to get background colours'''
        colour = self.background[self.b_ix]
        self.b_ix = (self.b_ix + 1)%len(self.background)
        return colour
        
    def get_accent(self):
        for color in self.accent:
            yield color

    def get_custom(self):
        '''Function to get custom colours'''
        colour = self.custom[self.c_ix]
        self.c_ix = (self.c_ix + 1)%len(self.accent)
        return colour
    
    def set_pub(self):
        plt.rcParams.update({
            "lines.linewidth": 1.5,
            "grid.color": "0.5",
            "grid.linestyle": "-",
            "grid.linewidth": 0.5,
            "savefig.dpi": 300,
            "axes.titlesize": 16,
            "axes.labelsize": 12,
            "axes.labelweight": "bold",
            "legend.fontsize": 12,
            "xtick.labelsize": 12,
            "ytick.labelsize": 12,
            "axes.prop_cycle": cycler(color=self.accent),
        })
        