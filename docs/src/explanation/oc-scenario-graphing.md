# OC Scenario Graphing
This document explains the internals of how Tornium graphs the edges and nodes of OC scenario graphs from user-provided data.

Each OC type is represented as a graph of the decision nodes presented by the graph: $$G = (V, E)$$ with each $V$ having a set of $V'$. Each $V$ is a decision node of the OC scenario -- where some subset of the users in the OC are used to probabilistically determine if the user has passed the node -- represented with a node of the graph. Each $v \in V$ of the graph contains a set of $V'$ of $$|V'| \geq 1$$ where each $$v' \in V'_v$$ represents a possible narration of the node $v$.

For every $e \in E$ of the graph and for every $v' \in V'_v$ of the node $v \in V$, each $e$ and $v'$ has a counter $i_e$ and $i_{v'}$ respectively. Whenever the $e$ edge or $v'$ narration variant is "verified" by a user pushing the data containing the node, the $i_e$ and $i_{v'}$ counters for the edge and narration variant respectively is incremented. Every other edge of $G$ and every other narration variant for the node $v$ not verified in this data push is exponentially decayed by some equation such as $$  $$. NOTE: This must run atomically to ensure that exponential decay works properly.

At some regular time period, e.g. daily, every $e \in E$ of $G$ and $v' \in V'$ would be pruned to remove nodes where the counter is below some threshold. This ensures that older data that is no longer valid and data that is invalid (either through a bug or maliciously inserted) is removed.

When snapshotting the scenario graph, we want to find some subset of $G$ that is binary at each decision node with one narration variant $v'$ per $v$. Preferably, $G$ would already be binary with one narration variant per node due to the pruning of data below the threshold. However, this is not guaranteed. We can assume that selecting nodes and narration variant, where there are too many, by the highest $i$ will provide sufficiently accurate snapshot of $G$.
