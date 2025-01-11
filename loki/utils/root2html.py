# encoding: utf-8
"""
loki.utils.root2html.py
~~~~~~~~~~~~~~~~~~~~~~~
Generates html and images for displaying TCanvases.
Created by Ryan Reece and Tae Min Hong and later ported into the 
loki framework, with minor adjustments by Will Davey.

DESCRIPTION 
    root2html is a script for generating an html page for displaying plots.
    root2html expects you to pass a root file, filled with TCanvases,
    possibly organized in TDirectories.  The canvases presumably have plots
    that you have pre-made and styled however you like.  root2html inspects
    the root file and walks its directories.  Then, for each canvas, it
    inspects  all objects that have been drawn to the canvas, and gets
    statistics depending on the object's type.  These stats are displayed in
    the caption when you click on a figure.  Then, root2html creates eps and
    gif/png images for each of the plots, and generates an html page
    containing and linking all the information.
    
    When viewing the output html, note that you can click-up more than one
    figure at a time, and drag them around the screen.  That javascript magic
    is done with the help of this library: http://highslide.com/.

INSTALLATION
    Assuming you have a working ROOT installation with PyROOT, the only other
    requirement is that you download the highslide javascript library at
    http://highslide.com/, unzip it, and set the highslide_path variable to
    point to the path: highslide-<version>/highslide (see below).

SEE ALSO

* ROOT <http://root.cern.ch>
* Highslide <http://highslide.com/>

"""
__author__    = "Ryan Reece <ryan.reece@cern.ch>, Tae Min Hong  <tmhong@cern.ch>"
__created__   = "2011"
__copyright__ = "Copyright 2011 The authors"
__license__   = "GPL <http://www.gnu.org/licenses/gpl.html>"


#------------------------------------------------------------------------------

import copy
import ctypes
import os, sys, getopt
import shutil
import time
import re
import math
import ROOT
from .dev import DevTool


#------------------------------------------------------------------------------

## global options
quiet = True


#______________________________________________________________________________=buf=
def subparser_webbook(subparsers):
    """Subparser for *loki webbook*"""
    parser = subparsers.add_parser("webbook", help="compile images into web book (root2html)", description="Compile images into web book using root2html")
    parser.add_argument("rootfile", nargs=1, metavar="FILE", help="Input ROOT FILE")
    parser.add_argument( "-t", "--tag", dest="tag", required=True,
            metavar="TAG", help="Identifier string for webbook" )
    parser.add_argument( "-j", "--highslide", dest="highslide", default="../../highslide/highslide", 
            metavar="PATH", help="PATH to highslide installation" )
    parser.add_argument( "-p", "--pattern", dest="pattern", metavar="REGEX", default = '',
            help="Regex pattern for filtering the TCanvas paths processed.  The pattern is matched against the full paths of the TCanvases in the root file." )
    parser.add_argument( "--nopub", dest="publish", action="store_false", default=True,
            help="Don't ask to publish webbook to loki server" )
    parser.add_argument( "-k", "--keep", dest="keep", action="store_true",
            help="Keep local webbook copy" )
    parser.add_argument( "-s", "--server", dest="server", 
            metavar="AFSPATH", help="AFSPATH to private server" )        
    parser.set_defaults(command=command_webbook)


#______________________________________________________________________________=buf=
def command_webbook(args):
    """Subcommand for *loki webbook*"""

    ROOT.gROOT.SetBatch(True)
    #try:
    #    import rootlogon # your custom ROOT options, comment-out this if you don't have one
    #except:
    #    print('Could not import rootlogon')
    ROOT.gErrorIgnoreLevel = 1001

    ## options
    pattern = args.pattern
    highslide_path = args.highslide
    rootfile = args.rootfile[0]
    tag = args.tag    
    server = args.server
  
    ## construct basename 
    date = time.strftime('%Y-%m-%d',time.localtime())
    user = os.environ['USER']
    basename = "{date}_{user}_{tag}".format(
        date = date,
        user = user,
        tag  = tag)

    ## build webbook
    t_start = time.time()
    path = rootfile
    print("path: ", path)
    name = os.path.join(basename, 'index.html')
    index = HighSlideRootFileIndex(name,highslide_path=highslide_path)
    index.write_head(name)
    n_plots = index.write_root_file(path, pattern)
    index.write_foot()
    index.close()
    print(f'  {name} written.')

    # build summary
    t_stop = time.time()
    print('  # plots    = %i' % n_plots)
    print('  time spent = %i s' % round(t_stop-t_start))
    print('  avg rate   = %.2f Hz' % (float(n_plots)/(t_stop-t_start)))
    print('  Done.')
    
    # publish webbbok
    publish = False
    if server: publish = True
    elif args.publish:        
        # ask to publish?        
        while True: 
            result = raw_input("Publish to loki server? [Y/n]:")
            if result.lower() not in ["","n","y"]: 
                print("Invalid option!")
                continue
            if result.lower() in ["","y"]:   
                publish = True
            break    
        
    # publish
    exit_code = 0
    if publish:     
        tool = DevTool()
        if server is None: 
            if not tool.publish_webbook(basename):
                print("Failed to publish to loki server.")
                exit_code = 1 
            else:
                url = os.path.join(tool.server_webbook_url(),basename)
                print("Successfully published to loki server.")
                print(f"Webbook available at {url}")
        else: 
            if not tool.publish_webbook(basename,server):
                print(f"Failed to publish to {server}")
                exit_code = 1 
            else:
                url = os.path.join(tool.server_webbook_url(),basename)
                print(f"Successfully published to {server}")
        
    # clean local area
    if not args.keep: 
        print("Cleaning local area...")
        shutil.rmtree(basename, ignore_errors=True)
    
    exit(exit_code)

#------------------------------------------------------------------------------
class HighSlideRootFileIndex():
    """Class that converts ROOT files into html
    
    :param name: html index file name
    :type name: str
    :param highslide_path: path to highslide installation
    :type highslide_path: str
    :param dohist: make images for lone histograms
    :type dohist: bool
    :param img_format: image format to use (eg. png, eps...)
    :type img_format: str
    :param img_height: image height in pixels
    :type img_height: int
    :param thumb_height: thumb-nail height in pixels
    :type thumb_height: int
    """
    #__________________________________________________________________________
    def __init__(self, 
                 name='index.html', 
                 highslide_path=None, 
                 dohist=False,
                 img_format = 'png', 
                 img_height = 600, 
                 thumb_height = 60,
            ):
        make_dir_if_needed(name)
        super(HighSlideRootFileIndex, self).__init__(name, 'w')
        self.dirname = os.path.dirname(name)
        self.highslide_path = highslide_path 
        self.previous_level = 0
        self.pwd = None
        self.dohist = dohist
        self.img_format = img_format
        self.img_height = img_height
        self.thumb_height = thumb_height
        
    #__________________________________________________________________________
    def write_head(self, title):
        head_template = r"""<!DOCTYPE html PUBLIC "-//W3C//DTD XHTML 1.0 Strict//EN"
    "http://www.w3.org/TR/xhtml1/DTD/xhtml1-strict.dtd">
<html xmlns="http://www.w3.org/1999/xhtml" xml:lang="en" lang="en">
<head>
    <title>%(title)s</title>
    <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
    <script type="text/javascript" src="%(highslide_path)s/highslide-full.js"></script>
    <link rel="stylesheet" type="text/css" href="%(highslide_path)s/highslide.css" />
    <script type="text/javascript">
        //<![CDATA[
        hs.graphicsDir = '%(highslide_path)s/graphics/';
        hs.wrapperClassName = 'wide-border';
        //]]>
    </script>
    <script type="text/javascript">
        //<![CDATA[
        function toggle_more(objID) {
            if (!document.getElementById) return;
            var ob = document.getElementById(objID).style;
            ob.display = (ob.display == 'block')?'none':'block';
            var ob2 = document.getElementById('link:'+objID);
            ob2.className = (ob2.className == 'open') ? 'closed' : 'open';
        }
        //]]>
    </script>
    <style type="text/css">
        <!--
        body
        {
            font-family: sans-serif;
        }
        h1
        {
            display: block;
            border-bottom: 1px black solid;
            padding-bottom: 5px;
            font-size: 1.0em;
        }
        div.dir_header
        {
            font-size: 1.5em;
        }
        div.dir_header a, div.highslide-heading a
        {
            cursor: pointer;
        }
        div.dir_header a.open:before
        {
            font-family: monospace;
            content: "[-] ";
        }
        div.dir_header a.closed:before
        {
            font-family: monospace;
            content: "[+] ";
        }
        div.more
        {
            display: none;
            clear: both;
            margin-left: 40px;
        }
        div.foot
        {
            display: block;
            margin-top: 5px;
            border-top: 1px black solid;
            padding-top: 5px;
            padding-bottom: 15px;
        }
        div.foot div.user, div.foot div.date
        {
            display: inline;
            float: left;
            margin-right: 40px;
        }
        div.foot div.powered_by, div.foot div.valid
        {
            display: inline;
            float: right;
            margin-left: 40px;
        }
        a:link {color: #06989a;}
        a:visited {color: #bf2dae;}
        a:hover {text-decoration: underline;}
        table td, table th
        {
            padding-top: 0;
            padding-bottom: 0;
            padding-left: 0px;
            padding-right: 20px;
            font-family: monospace;
            font-size: 10px;
            text-align: right;
        }
        /*
        table td+td, table th+th
        {
            text-align: right;
        }
        */
        table th
        {
            font-weight: bold;
        }
        -->
    </style>
</head>
<body>
<div id="body">
"""
        self.write(head_template % {
                'title' : title,
                'highslide_path' : self.highslide_path })
    #__________________________________________________________________________
    def write_foot(self):
        ## close preivous more divs
        while self.pwd:
            self.write("</div> <!-- %s -->\n" % self.pwd)
            pwd_split = self.pwd.split('/')[:-1]
            if pwd_split:
                self.pwd = os.path.join(*(pwd_split))
            else:
                self.pwd = ''
        foot_template = r"""
</div> <!-- body -->
<div class="foot">
    <div class="user">%(user)s</div>
    <div class="date">%(date)s</div>
    <div class="powered_by">produced with <a href="https://svnweb.cern.ch/trac/penn/browser/reece/rel/root2html/trunk/root2html.py">root2html.py</a></div>
    <div class="valid"><a href="http://validator.w3.org/check?uri=referer">valid xhtml</a></div>
</div>
</body>
</html>
"""
        self.write(foot_template % {
                'user' : os.environ['USER'],
                'date' : time.ctime() })
    #__________________________________________________________________________
    def write_root_file(self, path, pattern=''):
        n_plots = 0
        rootfile = ROOT.TFile(path)
        for dirpath, dirnames, filenames, tdirectory in walk(rootfile):
            for key in filenames:
                obj = tdirectory.Get(key)

                # Hack for when we find TH1, TH2 instead of TCanvas
                new_obj = None
                if self.dohist and (issubclass(obj.__class__, ROOT.TH1) or issubclass(obj.__class__, ROOT.TH1)):
                #if issubclass(obj.__class__, ROOT.TH1) or issubclass(obj.__class__, ROOT.TH1):
                    new_obj = ROOT.TCanvas(obj.GetName(), obj.GetTitle(), 500, 500)
                    new_obj.cd()
                    obj.Draw()
                    obj = new_obj

                # Put TCanvas on html
                if isinstance(obj, ROOT.TCanvas):
                    root_dir_path = dirpath.split(':/')[1]
                    root_key_path = os.path.join(root_dir_path, key)
                    if pattern and not re.match(pattern, root_key_path):
                        continue
                    print(os.path.join(dirpath, key))
                    self.write_dir_header(dirpath)
                    full_path = os.path.join(self.dirname, root_key_path)
                    self.write_canvas(obj, full_path)
                    n_plots += 1

        rootfile.Close()
        return n_plots
    #__________________________________________________________________________
    def write_dir_header(self, path):
        path_split = path.split(':/')
        rootfile = path_split[0]
        dirpath = path_split[1]
        dirpath.rstrip('/')

        if self.pwd is None:
            #self.write("""\n<h1>%s</h1>\n""" % rootfile)
            self.write("""\n<h1>%s</h1>\n""" % self.dirname)
            self.pwd = ''

        if dirpath != self.pwd:
            ## pop
            rel_path = relpath(dirpath, self.pwd)
            while rel_path.startswith('../'):
                self.write("</div> <!-- %s -->\n" % self.pwd)
                self.pwd = os.path.join(*(self.pwd.split('/')[:-1])) if self.pwd.count('/') else ''
                rel_path = relpath(dirpath, self.pwd)

            ## push
            rel_path = relpath(dirpath, self.pwd)
            while rel_path.count('/'):
                path_down_one_dir = '%s:/%s' % (rootfile, os.path.join(self.pwd, rel_path.split('/')[0]))
                self.write_dir_header(path_down_one_dir)
                rel_path = relpath(dirpath, self.pwd)

            id_name = dirpath.replace('/', '_')
            dir_name = dirpath.split('/')[-1]
            self.write("""\n<div class="dir_header"><a id="link:%s" class="closed" onclick="toggle_more('%s')">%s</a></div>\n""" % (id_name, id_name, dir_name))
            self.write("""<div id="%s" class="more">\n""" % id_name)
            self.pwd = dirpath
    #__________________________________________________________________________
    def write_canvas(self, canvas, basepath):
        name = canvas.GetName()
        make_dir_if_needed(basepath)
        ## save eps
        eps = basepath + '.eps'
        canvas.SaveAs(eps)
        ## save img
        if self.img_format == 'gif':
            img = self.convert_eps_to_gif(eps)
        elif self.img_format == 'png':
            img = eps.replace(".eps", ".png")
            copy.copy(canvas).SaveAs(img)
        elif self.img_format == 'svg':
            img = eps.replace('.eps', '.svg')
            copy.copy(canvas).SaveAs(img)
            ## retrieve svg width, heigth (smaller than canvas)
            with open(img, "r") as svg:
                for line in svg:
                    if line.startswith("<svg"):
                        svg_width  = int(1.05*float(re.search('width="(\d*)"' , line).group(1)))
                        svg_height = int(1.15*float(re.search('height="(\d*)"', line).group(1)))
                        break
                    else:
                        continue
        ## save thumb
        if self.img_format == 'gif':
            thumb = self.convert_eps_to_thumb_gif(eps)
        elif self.img_format == 'png':
            thumb = img
        elif self.img_format == 'svg':
            thumb = img.replace('.svg', '.png')
            copy.copy(canvas).SaveAs(thumb)
        ## additional formats, see <http://root.cern.ch/root/html/TPad.html#TPad:SaveAs>
        formats = ['.pdf'] # ['.png', '.pdf', '.C']
        for format in formats:
            copy.copy(canvas).SaveAs(basepath + format)
        ## convert to relpaths
        ## use locally defined relpath because os.path.relpath does not
        ## exist in Python 2.5.
        eps = relpath(eps, self.dirname)
        pdf = eps.replace(".eps", ".pdf")
        img = relpath(img, self.dirname)
        thumb = relpath(thumb, self.dirname)
        ## vector graphics (svg) need a special hyperlink tag
        if not self.img_format == 'svg':
            hreftag = """ class="highslide" rel="highslide" """
        else:
            hreftag = """ onclick="return hs.htmlExpand(this, {objectType: 'iframe', height: %s, width: %s})" """ % (svg_height, svg_width)
        ## write xhtml
        fig_template = r"""
        <a href="%(img)s" %(hreftag)s>
        <img src="%(thumb)s" alt="%(name)s" title="%(name)s" height=%(thumb_height)s/></a>
        """
        heading_template = r"""<div class="highslide-heading">
        <a title="%(path)s">%(name)s</a>&nbsp;[&nbsp;<a href="%(eps)s">eps</a>&nbsp;|&nbsp;<a href="%(pdf)s">pdf</a>&nbsp;]
        </div>
        """
        caption_template = r"""<div class="highslide-caption">
        %s</div>
        """
        self.write(fig_template % {
                'name'         : name,
                'img'          : img,
                'hreftag'      : hreftag,
                'thumb_height' : self.thumb_height,
                'thumb'        : thumb })
        self.write(heading_template % {
                'path'  : basepath,
                'name'  : name,
                'eps'   : eps,
                'pdf'   : pdf,
                'img'   : img,
                'format': self.img_format})
        ## get stats
        stats = get_canvas_stats(canvas)
        if stats:
            clean_stats_names(stats)
            tab = convert_stats_to_table(stats)
            html_tab = convert_table_to_html(tab)
            self.write(caption_template % html_tab)

    #______________________________________________________________________________
    def convert_eps_to_gif(self,eps):
        assert eps.endswith('.eps')
        name = eps[:-3] + 'gif'
        os.system('convert -format gif %s[x%i] %s' % (eps, self.img_height, name) )
        if not quiet:
            print('  Created %s' % name)
        return name

    #______________________________________________________________________________
    def convert_eps_to_thumb_gif(self,eps):
        assert eps.endswith('.eps')
        name = eps[:-3] + 'thumb.gif'
        os.system('convert -resize x%i -antialias -colors 64 -format gif %s %s' % (self.thumb_height, eps, name) )
        if not quiet:
            print('  Created %s' % name)
        return name

    """
    #______________________________________________________________________________
    def convert_eps_to_png(self,eps):
        assert eps.endswith('.eps')
        name = eps[:-3] + 'png'
        os.system('convert -resize x%i -antialias -colors 64 -format png %s %s' % (self.img_height, eps, name) )
        if not quiet:
            print('  Created %s' % name)
        return name

    #______________________________________________________________________________
    def convert_eps_to_thumb_png(self,eps):
        assert eps.endswith('.eps')
        name = eps[:-3] + 'thumb.png'
        os.system('convert -resize x%i -antialias -colors 64 -format png %s %s' % (self.thumb_height, eps, name) )
        if not quiet:
            print('  Created %s' % name)
        return name
    """





#------------------------------------------------------------------------------
# free functions
#------------------------------------------------------------------------------

#__________________________________________________________________________
def get_canvas_stats(canvas):
    prims = [ p for p in canvas.GetListOfPrimitives() ]
    prims.reverse() # to match legend order
    names_stats = []
    for prim in prims:
        if isinstance(prim, ROOT.TFrame):
            continue # ignore these
        elif isinstance(prim, ROOT.TPad):
            names_stats.extend( get_canvas_stats(prim) )
        else:
            names_stats.extend( get_object_stats(prim) )
    return names_stats

#__________________________________________________________________________
def get_object_stats(h):
    names_stats = []
    name = h.GetName()
    stats = {}
    if isinstance(h, ROOT.TH1) and not isinstance(h, ROOT.TH2):
        nbins       = h.GetNbinsX()
        entries     = h.GetEntries()
        err = ctypes.c_double(0)
        integral    = h.IntegralAndError(0, nbins+1, err)
#        integral    = h.Integral(0, nbins+1)
#        err         = math.sqrt(float(entries))*integral/entries if entries else 0
        mean        = h.GetMean()
        rms         = h.GetRMS()
        under       = h.GetBinContent(0)
        over        = h.GetBinContent(nbins+1)
        stats['entries'] = '%i'   % round(entries)
        stats['int']     = ('%i' % round(integral)) if integral > 100 else ('%.3g' % integral)
        stats['err']     = '%.3g' % err
        stats['mean']    = '%.3g' % mean
        stats['rms']     = '%.3g' % rms
        stats['under']   = '%.3g' % under
        stats['over']    = '%.3g' % over
        names_stats.append( (name, stats) )
    elif isinstance(h, ROOT.TH2):
        nbins_x     = h.GetNbinsX()
        nbins_y     = h.GetNbinsY()
        entries     = h.GetEntries()
        err = ctypes.c_double(0)
        integral    = h.IntegralAndError(0, nbins_x+1, 0, nbins_y+1, err)
#        integral    = h.Integral(0, nbins_x+1, 0, nbins_y+1)
#        err         = math.sqrt(float(entries))*integral/entries if entries else 0
        mean_x      = h.GetMean(1)
        rms_x       = h.GetRMS(1)
        mean_y      = h.GetMean(2)
        rms_y       = h.GetRMS(2)
        stats['entries'] = '%i'   % round(entries)
        stats['int']     = ('%i' % round(integral)) if integral > 100 else ('%.3g' % integral)
        stats['err']     = '%.3g' % err
        stats['mean_x']  = '%.3g' % mean_x
        stats['rms_x']   = '%.3g' % rms_x
        stats['mean_y']  = '%.3g' % mean_y
        stats['rms_y']   = '%.3g' % rms_y
        names_stats.append( (name, stats) )
    elif isinstance(h, ROOT.TGraph) \
            or isinstance(h, ROOT.TGraphErrors) \
            or isinstance(h, ROOT.TGraphAsymmErrors):
        if not quiet:
            print('WARNING: HighSlideRootFileIndex.get_object_stats( %s ) not implemented.' % type(h))
    elif isinstance(h, ROOT.THStack):
        stack_stats = get_object_stats( h.GetStack().Last() )
        assert len(stack_stats) == 1, type(h.GetStack().Last())
        stack_stats[0] = ('stack sum', stack_stats[0][1]) # reset name
        names_stats.extend( stack_stats )
        stack_hists_stats = []
        for hist in h.GetHists():
            stack_hists_stats.extend( get_object_stats(hist) )
        stack_hists_stats.reverse()
        names_stats.extend(stack_hists_stats)
    else:
        if not quiet:
            print('WARNING: HighSlideRootFileIndex.get_object_stats( %s ) not implemented.' % type(h))
    return names_stats

#__________________________________________________________________________
def clean_stats_names(names_stats):
    """Removes a common postfix from any of the names in the stats."""
    name = names_stats[-1][0]
    postfix = None
    sep = '__'
    if name.count(sep):
        postfix = name.split(sep)[-1]
    if postfix:
        for i in xrange(len(names_stats)):
            name, stats = names_stats[i]
            if name.endswith(sep+postfix):
                name = '__'.join(name.split(sep)[0:-1])
                names_stats[i] = (name, stats)

#__________________________________________________________________________
def convert_stats_to_table(names_stats):
    ## hack, need to come up with a way to determine which stats to expect,
    ## and how to organize the table(s)
    if names_stats[0][1].has_key('rms_x'): # TH2
        top_row = ['name', 'entries', 'int', 'err', 'mean_x', 'rms_x', 'mean_y', 'rms_y']
    else:
        top_row = ['name', 'entries', 'int', 'err', 'mean', 'rms', 'under', 'over']
    tab = [top_row]
    for name, stats in names_stats:
        row = []
        for x in top_row:
            if x == 'name':
                row.append(name)
            else:
                row.append( stats.get(x, '') )
        tab.append(row)
    return tab

#__________________________________________________________________________
def convert_table_to_html(tab):
    html = ['    <table>\n']
    is_first = True
    for row in tab:
        html += ['        <tr>']
        for i_col, col in enumerate(row):
            row[i_col] = check_for_too_long_mouse_over(str(col))
        if is_first:
            for col in row:
                html += ['<th>%s</th>' % col]
            is_first = False
        else:
            for col in row:
                html += ['<td>%s</td>' % col]
        html += ['</tr>\n']
    html += ['    </table>\n']
    html = ''.join(html)
    return html

#__________________________________________________________________________
def check_for_too_long_mouse_over(s, limit=20):
    if len(s) > limit:
        return '<a title="%s" class="too_long">%s...</a>' % (s, s[:limit-3])
    return s

#______________________________________________________________________________
def walk(top, topdown=True):
    """
    os.path.walk like function for TDirectories.
    Return 4-tuple: (dirpath, dirnames, filenames, top): 
    
    * dirpath = 'file_name.root:/some/path' # may end in a '/'?
    * dirnames = ['list', 'of' 'TDirectory', 'keys']
    * filenames = ['list', 'of' 'object', 'keys']
    * top = this level's TDirectory
    """
# - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - - -
    assert isinstance(top, ROOT.TDirectory)
    names = [k.GetName() for k in top.GetListOfKeys()]
    dirpath = top.GetPath()
    dirnames = []
    filenames = []
    ## filter names for directories
    for k in names:
        d = top.Get(k)
        if isinstance(d, ROOT.TDirectory):
            dirnames.append(k)
        else:
            filenames.append(k)
    ## sort
    dirnames.sort()
    filenames.sort()
    ## yield
    if topdown:
        yield dirpath, dirnames, filenames, top
    for dn in dirnames:
        d = top.Get(dn)
        for x in walk(d, topdown):
            yield x
    if not topdown:
        yield dirpath, dirnames, filenames, top

#______________________________________________________________________________
def strip_root_ext(path):
    reo = re.match('(\S*?)(\.canv)?(\.root)(\.\d*)?', path)
    assert reo
    return reo.group(1)

#______________________________________________________________________________
def make_dir_if_needed(path):
    if path.count('/'):
        dirname = os.path.split(path)[0]
        if not os.path.isdir(dirname):
            os.makedirs(dirname)

#______________________________________________________________________________
def relpath(path, start='.'):
    """
    Return a relative version of a path
    Stolen implementation from Python 2.6.5 so I can use it in 2.5
    http://svn.python.org/view/python/tags/r265/Lib/posixpath.py?revision=79064&view=markup
    """
    # strings representing various path-related bits and pieces
    curdir = '.'
    pardir = '..'
    extsep = '.'
    sep = '/'
    pathsep = ':'
    defpath = ':/bin:/usr/bin'
    altsep = None
    devnull = '/dev/null'

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(sep)
    path_list = os.path.abspath(path).split(sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = [pardir] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return '.'
    return os.path.join(*rel_list)


