import matplotlib.pyplot as plt


def visualize(net, filename='result.pdf', map=None):
    fig, ax = plt.subplots(figsize=(20, 20))
    ax.set_xlim([0, 1000])
    ax.set_ylim([0, 1000])
    for i in range(len(net.targets)):
        ax.add_patch(plt.Circle((net.targets[i].x, net.targets[i].y), net.r, color='r', alpha=0.2))
    plt.scatter([net.targets[i].x for i in range(len(net.targets))],
                [net.targets[i].y for i in range(len(net.targets))],
                marker='*', color='r', label='Target')
    sList = net.sList + net.relay_nodes
    plt.scatter([sList[i].x for i in range(len(sList))],
                [sList[i].y for i in range(len(sList))],
                marker='^', color='b', label='Sensor')
    plt.plot([net.Base.x], [net.Base.y], 'yv', markersize=12, label='Base station')
    ax.set_aspect(1)
    if map is not None:
        ax.imshow(map, extent=[0, 1000, 0, 1000])
    plt.legend()
    plt.savefig(filename)
    plt.show()
