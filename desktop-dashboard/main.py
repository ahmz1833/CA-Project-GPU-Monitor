import sys

import App.logic.Logic
import App.main as app

if __name__ == '__main__':
    if len(sys.argv) > 1:
        App.logic.Logic.GPUMonitor.URL = sys.argv[1]
    app.main()
