import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Use MCMC Simulation to determine the likelihood that a particular district is an outlier by the efficiency gap metric')
    parser.add_argument('file_path', metavar='N', type=int, nargs='+',
                        help='an integer for the accumulator')
    args = parser.parse_args()


