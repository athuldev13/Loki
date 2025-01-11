# loki

Loki (Lots of Kewl Images) is a python package designed to make 
tau performance plots and to train/tune tau algorithms 
using MxAOD datasets output by
[THOR](https://gitlab.cern.ch/atlas-perf-tau/THOR/-/blob/master/README.rst).

See the [loki web documenation](https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main)
for a comprehensive overview and instructions.  


## Quick Start
### Prerequisites and Installation 
On lxplus do: 
    
    setupATLAS
    lsetup "root 6.28.10-x86_64-el9-gcc13-opt"

and then:

    cd loki 
    source setup.sh

Make sure you **source the setup each time you enter a new shell!**    

### Run 
Start with examples: 

    cd examples
    python example01_basics.py 
    
For more detailed instructions see the [quickstart](https://atlas-tau-loki.web.cern.ch/atlas-tau-loki/main/quickstart.html)

### Documentation
Detailed documentation can be found on this [linnk](https://atlas-tau-loki.web.cern.ch/main/)

## Tutorial

Slides from the 2021 tutorial [link](https://indico.cern.ch/event/1074654/contributions/4642085/attachments/2362613/4033453/loki_tut_2021.pdf)

Slides from the 2024 tutorial [link](https://indico.cern.ch/event/1372592/contributions/5860165/)

## Support <a name="support"></a>

[Mattermost: SOS THOR/loki](https://mattermost.web.cern.ch/atlas-tauwg/channels/thor-loki)

You'll need to [sign-up](https://mattermost.web.cern.ch/signup_user_complete/?id=zwjt76grwbny5d51k6iff1uxer) to the TauCP Mattermost team. 


## Contributing

We use Git ([gitlab.cern.ch](https://gitlab.cern.ch)) for development.
The xTauFramework provides a very nice [Git README](https://gitlab.cern.ch/ATauLeptonAnalysiS/xTauFramework/blob/master/doc/README_GIT.md)
explaining the workflow. A brief summary is given here, with loki specific links:  

1. Fork ([make your own fork](https://gitlab.cern.ch/atlas-perf-tau/loki/forks/new) of the project)
2. Clone (make local clone of the project) ```git clone ssh://git@gitlab.cern.ch:7999/<username>/loki.git```
3. Branch (make branch for your new feature)
4. Commit (locally commit your changes)
5. Push (push changes to your fork)
6. Merge ([submit pull request](https://gitlab.cern.ch/atlas-perf-tau/loki/merge_requests) from your fork to main repo)
7. Switch back to master and pull from upstream

If you have any questions, [contact support](#support)


## Contributors

* **Will Davey** ([will.davey@cern.ch](mailto:will.davey@cern.ch)) - main developer (not in ATLAS anymore)
* **Chris Deutsch** ([christopher.deutsch@cern.ch](mailto:christopher.deutsch@cern.ch)) - training implementation (not in ATLAS anymore)
* **Antonio de Maria** ([antonio.de.maria@cern.ch](mailto:antonio.de.maria@cern.ch))
* **Michaela Mlynarikova** ([michaela.mlynarikova@cern.ch](mailto:michaela.mlynarikova@cern.ch))

## License

See [LICENSE](LICENSE.md)
