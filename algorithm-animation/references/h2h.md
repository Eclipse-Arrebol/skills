# H2H语义与数值参考

`Bag(v)={v}∪N_remaining(v)`。画面`SC(v)`是v消除前到全部剩余邻居的带权邻接表，代码`upward[v]`保存原边、此前填充边及松弛后的权重。经v形成的邻居对候选另存`fill_candidates`，不能替代SC。先冻结邻接快照，再删除工作图节点；后续增添L时不覆盖SC。

`L(v,a)`是v到祖先a的全图最短距离，不必等于对应SC值，也不是沿树边累加。

## 已验证六点案例（教学数值）

原边AB2、BC3、CD2、DE3、EF2、AF4、BE5、CF6；消除序A→D→B→C→E→F，符合当前最小度、同度字母序。parent取剩余邻居中次序最靠前者：A→B、D→C、B→C、C→E、E→F，F根。

| v | Bag | SC | L，省略非根自身0 |
|---|---|---|---|
| A | A,B,F | B:2 F:4 | B:2 C:5 E:6 F:4 |
| D | D,C,E | C:2 E:3 | C:2 E:3 F:5 |
| B | B,C,E,F | C:3 E:5 F:6 | C:3 E:5 F:6 |
| C | C,E,F | E:5 F:6 | E:5 F:6 |
| E | E,F | F:2 | F:2 |
| F | F | ∅ | F:0 |

E虽无邻居对补边，SC仍须保存EF=2。B的SC同时有原边BC／BE和已生成的BF shortcut；A必须保存AB2、AF4，不能只显示它生成的BF6。

## 递推与来源就绪

自根向叶算`L(v,a)=min_u[SC(v,u)+d(u,a)]`，u遍历保存邻居。在无向案例中，u和a都在祖先链上，d(u,a)从更深者到更浅者的已建立标签读取，u=a取0。

例如L(A,E)=min(2+5,4+2)=6：2、4来自SC(A)，5来自L(B,E)，2来自L(E,F)。让数据同时可见并标记实际来源。参考代码检查每次读取的条目已显示，不用Dijkstra代替标签构建；Dijkstra仅作独立核验。

## 动态AB2→9

固定拓扑和次序，树与Bag不变。先更新SC(A)的B:9，BF shortcut重算13并更新SC(B)的F:13；CF、EF复核仍6、2，不继续发变化通知。此时旧L仍可见。

再重算L(B,F)=min(3+6,5+2,13+0)=7、L(A,B)=9、L(A,C)=10；其余不变。SC(B,F)=13和L(B,F)=7必须能同时辨认。

query(A,D)用LCA=C的Bag{C,E,F}，初始7/9/9得7，更新12/9/9得9；路径分别A-B-C-D与A-F-E-D。新图需重算，不能沿用这些答案或传播范围。

## 来源和边界

Li等，*A CPU-GPU Hybrid Labelling Algorithm for Massive Shortest Distance Queries on Road Networks*，PVLDB18(3)，770–783，2024，[全文](https://www.vldb.org/pvldb/vol18/p770-li.pdf)，§2.2／PDF第2–3页，包含带权decomposition neighbors、父节点及标签递推。动态两阶段背景见Koehler等，*Stable Tree Labelling for Accelerating Distance Queries on Dynamic Road Networks*，EDBT2025，[全文](https://openproceedings.org/2025/conf/edbt/paper-127.pdf)，§3.1／PDF第3页。

参考有249项有限案例检查，六组邻接快照、21次显示计算；不是一般性证明、生产IncH2H／GPU实现或性能实验。修改参考图时还须更新其固定预期值和校验。
