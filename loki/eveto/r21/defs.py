# if you need to make any new variable defs, they should go here.
from loki.common import vars
from loki.core.var import Var
from loki.core.histutils import log_bins

# Output Variables
xmin = -1.01
xmax = 1.01
start = 0.01
w = xmax - xmin
bins_grad_bdt = list(reversed([xmax - (v - start) for v in log_bins(1000, start, start+w)]))
vars.NewEleBDTScore = Var("NewEleBDTScore").add_view(xbins=bins_grad_bdt, name="flat_r21")
vars.taus.pt.add_view(20, 20.e3,  1000.e3, do_logx=True, name="flat_r21")
vars.taus.absleadTrackEta.add_view(25,  0., 2.5, name="flat_r21")