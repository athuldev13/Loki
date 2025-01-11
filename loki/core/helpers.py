# encoding: utf-8
"""
loki.core.helpers
~~~~~~~~~~~~~~~~~

Assorted helper functions for loki
"""
__author__    = "Will Davey"
__email__     = "will.davey@cern.ch"
__created__   = "2016-02-20"
__copyright__ = "Copyright 2016 Will Davey"
__license__   = "GPL http://www.gnu.org/licenses/gpl.html"

## modules
import errno
import os
import sys
from array import array
import ROOT
from loki.core import enums
from loki.core.histutils import frange
from loki.core.logger import log, supports_color


# - - - - - - - - - - - globals - - - - - - - - - - - - #

# - - - - - - - - - - - class defs  - - - - - - - - - - - - #
#------------------------------------------------------------
class ProgressBar():
    #____________________________________________________________
    def __init__(self,ntotal=None,text=None,width=None):
        self.ntotal = ntotal
        self.text = text   
        self.width = width or 40

    #____________________________________________________________
    def update(self,n):
        """
        prints a progress bar
        """
        bar = f'[%-{self.width}s] %.f%%'
        frac = float(n)/float(self.ntotal)

        sys.stdout.write('\r')
        # the exact output you're looking for:
        inc = int(frac * float(self.width))
        line=enums.BLUEBOLD
        if self.text is not None:
            line+='%-17s:  '%(str(self.text)[:20])
        line+=bar % ('='*inc, frac*100.)
        line+=enums.UNSET
        sys.stdout.write(line)
        sys.stdout.flush()

    #____________________________________________________________
    def finalize(self):
        sys.stdout.write('\n')



# - - - - - - - - - - function defs - - - - - - - - - - - - #
#______________________________________________________________________________=buf=
def combine_weights(weights):
    """Returns product of *weight* strings to pass to TTree::Draw

    Each string is enclosed in parentheses and joined via the 
    product operator (`*`).

    :param weights: weight strings
    :type weights: str list
    :rtype: str
    """
    # enclose each weight with parentheses
    weights = [f"({w})" for w in weights]
    # multiple each weight
    weightstr = "*".join(weights)        
    return weightstr


#______________________________________________________________________________=buf=
def print_logo():
    """Unleash awesome loki logo"""
    if supports_color():
        color = enums.REDBOLD
        reset = enums.UNSET
    else: 
        color = ""
        reset = ""
            
    
    print(f"")
    print(f"    loki  Copyright (C) 2016 Will Davey")
    print(f"    This program comes with ABSOLUTELY NO WARRANTY;")
    print(f"")
    print(f"    /-------->>>> Unleashing brutal loki attack <<<<--------\\")
    print(f"    |{color}                                                       {reset}|")
    print(f"    |{color}           ___        ______    __   ___   __          {reset}|")
    print(f"    |{color}          |'  |      /    ' \\  |/'| /  ') |' \\         {reset}|")
    print(f"    |{color}          ||  |     // ____  \\ (: |/   /  ||  |        {reset}|")
    print(f"    |{color}          |:  |    /  /    ) :)|    __/   |:  |        {reset}|")
    print(f"    |{color}           \\  |___(: (____/ // (// _  \\   |.  |        {reset}|")
    print(f"    |{color}          ( \\_|:   \\        /  |: | \\  \\  /\\  |\\       {reset}|")
    print(f"    |{color}           \\_______)\\'_____/   (__|  \\__)(__\\_|_)      {reset}|")
    print(f"    |{color}  *(.                                                  {reset}|")
    print(f"    |{color}    .#*                                                {reset}|")
    print(f"    |{color}      *%*                                              {reset}|")
    print(f"    |{color}     (///%.                                            {reset}|")
    print(f"    |{color}    . ,&.##,                                           {reset}|")
    print(f"    |{color}     ,* /#/#/                                          {reset}|")
    print(f"    |{color}       /((&%(                  ./##.                   {reset}|")
    print(f"    |{color}          .#%/                (@@%%%,                  {reset}|")
    print(f"    |{color}           *(#              *%&&&(%#                   {reset}|")
    print(f"    |{color}             &(        ,.,/%&@@@##/#                   {reset}|")
    print(f"    |{color}             //      *&@&/(@&&@@&&@%%,                 {reset}|")
    print(f"    |{color}              %,    .%@&@@@@&&%%##(&%@#(               {reset}|")
    print(f"    |{color}              ,(   #&&%&%@#%&@@%.,%&%@#                {reset}|")
    print(f"    |{color}               (.*@&%&*  @@&@@&%&%&@@     /.,**        {reset}|")
    print(f"    |{color}                ##%//    *&@&@&&&&&&@@&%,*/#/#/(       {reset}|")
    print(f"    |{color}                (&%#     .&@@@&@@@@ #@%#/@#&%/         {reset}|")
    print(f"    |{color}               .*##*     /@@@@@@@@#   /,               {reset}|")
    print(f"    |{color}               /#%#.    *%@@@@@@@&&,                   {reset}|")
    print(f"    |{color}                 *&    *&&&@@@@@&&%%%(                 {reset}|")
    print(f"    |{color}                  %  .#&#&@@@@@&&%##                   {reset}|")
    print(f"    |{color}                  ,*.#&(%@@@@@@@@&&%%#&(               {reset}|")
    print(f"    |{color}                   #/&(#&@@@@@@@@@@@&%##%              {reset}|")
    print(f"    |{color}                   (%(%&@@@@@&&@@@@@&&@%%#/            {reset}|")
    print(f"    |{color}                  *%#%#%&@&&@@@@@&@@@@@@@@@&&(         {reset}|")
    print(f"    |{color}                .(%@(%&&@@@@@@@@@@@@@@@@@#&@@@.        {reset}|")
    print(f"    |{color}               .(&&&%#&@@@@@@&@@@@@@@@@@@%@@@@*        {reset}|")
    print(f"    |{color}              ,#&&@&&%&@@@@@@#&@@@@@@@@@@%,@@@#        {reset}|")
    print(f"    |{color}             .&&&&&&%%#@@@@@@/,@@@@@@@%@ .@&&          {reset}|")
    print(f"    |{color}             .@@@@&%%&(&@@@@&. &%,     &.   #@&/       {reset}|")
    print(f"    |{color}             (@@ %&%%% #    #.              %&&%%      {reset}|")
    print(f"    |{color}            ,@&(   (%   %                    .&@&%%.   {reset}|")
    print(f"    |{color}            %@&,         %,                     */,    {reset}|")
    print(f"    |{color}           *@&&.          .#                           {reset}|")
    print(f"    |{color}            ,/                                         {reset}|")
    print(f"    |{color}                                                       {reset}|")
    print(f"    \\_______________________________________________________/")
    print("")

    

 
      
    """            
    log().info("/-------->>>> Unleashing brutal loki attack <<<<--------\\")
    log().info("|{0}                                                       {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}           ___        ______    __   ___   __          {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}          |'  |      /    ' \\  |/'| /  ') |' \\         {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}          ||  |     // ____  \\ (: |/   /  ||  |        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}          |:  |    /  /    ) :)|    __/   |:  |        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}           \\  |___(: (____/ // (// _  \\   |.  |        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}          ( \\_|:   \\        /  |: | \\  \\  /\\  |\\       {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}           \\_______)\\'_____/   (__|  \\__)(__\\_|_)      {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}  *(.                                                  {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}    .#*                                                {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}      *%*                                              {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}     (///%.                                            {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}    . ,&.##,                                           {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}     ,* /#/#/                                          {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}       /((&%(                  ./##.                   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}          .#%/                (@@%%%,                  {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}           *(#              *%&&&(%#                   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}             &(        ,.,/%&@@@##/#                   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}             //      *&@&/(@&&@@&&@%%,                 {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}              %,    .%@&@@@@&&%%##(&%@#(               {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}              ,(   #&&%&%@#%&@@%.,%&%@#                {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}               (.*@&%&*  @@&@@&%&%&@@     /.,**        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                ##%//    *&@&@&&&&&&@@&%,*/#/#/(       {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                (&%#     .&@@@&@@@@ #@%#/@#&%/         {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}               .*##*     /@@@@@@@@#   /,               {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}               /#%#.    *%@@@@@@@&&,                   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                 *&    *&&&@@@@@&&%%%(                 {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                  %  .#&#&@@@@@&&%##                   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                  ,*.#&(%@@@@@@@@&&%%#&(               {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                   #/&(#&@@@@@@@@@@@&%##%              {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                   (%(%&@@@@@&&@@@@@&&@%%#/            {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                  *%#%#%&@&&@@@@@&@@@@@@@@@&&(         {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                .(%@(%&&@@@@@@@@@@@@@@@@@#&@@@.        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}               .(&&&%#&@@@@@@&@@@@@@@@@@@%@@@@*        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}              ,#&&@&&%&@@@@@@#&@@@@@@@@@@%,@@@#        {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}             .&&&&&&%%#@@@@@@/,@@@@@@@%@ .@&&          {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}             .@@@@&%%&(&@@@@&. &%,     &.   #@&/       {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}             (@@ %&%%% #    #.              %&&%%      {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}            ,@&(   (%   %                    .&@&%%.   {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}            %@&,         %,                     */,    {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}           *@&&.          .#                           {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}            ,/                                         {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("|{0}                                                       {1}|".format(enums.REDBOLD,enums.UNSET))
    log().info("\\_______________________________________________________/")
    log().info("")
    """


#______________________________________________________________________________=buf=
def set_palette(name=None, ncontours=200):
    """
    Set a color palette from a given RGB list
    stops, red, green and blue should all be lists of the same length
    see set_decent_colors for an example

    (may want this for migration matrices)
    """

    if name == "gray" or name == "grayscale":
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red   = [1.00, 0.84, 0.61, 0.34, 0.00]
        green = [1.00, 0.84, 0.61, 0.34, 0.00]
        blue  = [1.00, 0.84, 0.61, 0.34, 0.00]
    elif name == "green":
        stops = [0.00, 1.00]
        red   = [1.00, 0.00]
        green = [1.00, 1.00]
        blue  = [1.00, 0.00]
    elif name == "green2":        
        lvls = [(255,255,255),
                (229,245,224),
                (161,217,155),
                (49,163,84)]
        (stops,red,green,blue) = convert_rgb2root(lvls)        
    elif name == "blue":
        stops = [0.00, 1.00]
        red   = [1.00, 0.00]
        green = [1.00, 0.00]
        blue  = [1.00, 1.00]        
    elif name == "blue2":        
        lvls = [(255,255,255),
                (222,235,247),
                (158,202,225),
                (49,130,189)]        
        (stops,red,green,blue) = convert_rgb2root(lvls)
    elif name == "orange":        
        lvls = [(255,255,255),
                (254,230,206), 
                (253,174,107),
                (230,85,13),
                ]
        (stops,red,green,blue) = convert_rgb2root(lvls)
    elif name == "sunset":
        lvls = [(255,255,255),
                (255,237,160),
                (254,178,76),
                (240,59,32),
                ]
        (stops,red,green,blue) = convert_rgb2root(lvls)
    elif name == "pink":        
        lvls = [(255,255,255),
                (231,225,239),
                (201,148,199),
                (221,28,119),
                ]
        (stops,red,green,blue) = convert_rgb2root(lvls)
    elif name == "purple":
        lvls = [(255,255,255),
                (239,237,245),
                (188,189,220),
                (117,107,177)]
        (stops,red, green, blue) = convert_rgb2root(lvls)
    elif name == "light":
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red   = [1.00, 0.20, 0.00, 0.80, 1.00]
        green = [1.00, 0.10, 0.00, 0.10, 0.00]
        blue  = [1.00, 1.00, 0.50, 0.30, 0.00]
    elif name == "limit":
        stops = [0.00, 0.5076, 1.00]
        red   = [1.00, 1.00, 0.00]
        green = [1.00, 0.50, 0.00]
        blue  = [1.00, 0.50, 0.50]
    elif name == "5050":
        stops = [0.00, 0.5   , 1.00]
        red   = [1.00, 1.00, 0.00]
        green = [1.00, 0.50, 0.00]
        blue  = [1.00, 0.50, 0.50]
    else:
        stops = [0.00, 0.34, 0.61, 0.84, 1.00]
        red   = [0.00, 0.00, 0.87, 1.00, 0.51]
        green = [0.00, 0.81, 1.00, 0.20, 0.00]
        blue  = [0.51, 1.00, 0.12, 0.00, 0.00]

    s = array('d', stops)
    r = array('d', red)
    g = array('d', green)
    b = array('d', blue)

    npoints = len(s)
    ROOT.TColor.CreateGradientColorTable(npoints, s, r, g, b, ncontours)
    ROOT.gStyle.SetNumberContours(ncontours)


#______________________________________________________________________________=buf=
def convert_rgb2root(lvls):
    """Convert RGB-tuple per level into stops, r, g, b arrays for ROOT"""
    stops = list(frange(0., 1.01, 1.0 / float(len(lvls)-1)))
    red   = [float(r)/255. for (r,g,b) in lvls]
    green = [float(g)/255. for (r,g,b) in lvls]
    blue  = [float(b)/255. for (r,g,b) in lvls]                        
    return (stops, red, green, blue)


#______________________________________________________________________________=buf=
def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


#______________________________________________________________________________=buf=
def get_all_subclasses(cls):
    """Return all (defined) subclasses of base class *cls*
    
    http://stackoverflow.com/questions/3862310/how-can-i-find-all-subclasses-of-a-class-given-its-name
    """
    all_subclasses = []

    for subclass in cls.__subclasses__():
        all_subclasses.append(subclass)
        all_subclasses.extend(get_all_subclasses(subclass))

    return all_subclasses


## EOF
