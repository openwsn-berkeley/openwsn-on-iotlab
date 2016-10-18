import scale_parser
import scale_analyzer
import scale_plot

# ============== define ================

LOGFILE_PATH = '53865/'

def main():
    scale_parser.LogfileParser(LOGFILE_PATH)
    scale_analyzer.LogfileAnalyzer(LOGFILE_PATH)
    scale_plot.plotFigure(LOGFILE_PATH)
    
if __name__ == "__main__":
    main()