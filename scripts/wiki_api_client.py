
from utils import crawl, get_page_relationships
from build_network_graph import draw_graph_pyvis


def main():
    crawl(sim_threshold=.45)

    
if __name__ == '__main__':
    main()
