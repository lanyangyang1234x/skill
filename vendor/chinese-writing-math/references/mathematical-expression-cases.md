# 数学译稿的表达案例

以下 20 例的英文、直译和改稿均为本次自拟校准材料，不是李文威原文，也不是某部英语书的摘译。“直译”是供诊断的示意稿；自然译法可以不止一种。文中的引理号、节号与符号只属于各例的假设语境。用例支持[组句方法](mathematical-expression.md)，不作为数学事实库。

检索：长定语（E01–E02）；对象承接、动作（E03–E04）；定义（E05–E06）；证明任务（E07–E10）；抽象与具体（E11–E12）；公式（E13–E14）；限定与比较（E15–E17）；过渡与语气（E18–E20）。

## E01：把主语从多层定语中释放出来

**英文**：Let M be a finitely generated right R-module whose submodules are all projective. We shall use this hypothesis on submodules only in the proof of the converse.

**直译**：设 M 是一个其子模全部是投射的有限生成的右 R-模。我们将仅在逆向的证明中使用这一关于子模的假设。

**改稿**：设 M 是有限生成右 R-模，并假设 M 的每个子模都是投射模。关于子模的这一假设仅用于逆向的证明。

**取舍**：“有限生成右 R-模”是紧凑的对象类型，留作定语；对子模的条件另成分句。第二句仍紧接该假设，不把“仅用于”误写成“逆向成立当且仅当”。若源文中 this hypothesis 另有所指，先核前文再改。

## E02：保留关系从句中的待证身份

**英文**：We will construct a homomorphism f:M→N which we will later show to be surjective.

**直译**：我们将构造一个我们将在后面证明是满射的同态 f:M→N。

**改稿**：我们将构造同态 f:M→N，并在后文证明它是满射。

**取舍**：对象、构造和后续任务清楚分开。不能写成“取满同态 f”，因为存在性与满性都尚待建立。

## E03：让商映射承接核包含关系

**英文**：Let f:M→N be a homomorphism and let K be a submodule of M contained in ker f. Then f induces a homomorphism g:M/K→N. This homomorphism is injective if K=ker f.

**直译**：设 f:M→N 是同态，并且设 K 是 M 的一个被包含在 ker f 中的子模。于是 f 诱导一个同态 g:M/K→N。这个同态在 K=ker f 时是单射。

**改稿**：设 f:M→N 为同态，K 为 M 的子模且 K⊆ker f。于是 f 诱导同态 g:M/K→N。当 K=ker f 时，g 是单射。

**取舍**：用 g 接续前句新引入的对象；不将第二句的依据扩大为“f 是单射”。本例不补 g 的具体公式。

## E04：将动作落在动词上

**英文**：Restriction of f to U gives a map h:U→V. Applying the functor F to h gives the required morphism.

**直译**：f 到 U 的限制给出了一个映射 h:U→V。函子 F 对 h 的应用给出所要求的态射。

**改稿**：将 f 限制到 U，得到映射 h:U→V。对 h 应用函子 F，即得所需态射。

**取舍**：保留两步操作和各自的结果；不因第二句简短就写成“故 F 保持所需性质”，原文没有这种断言。

## E05：定义的条件与命名

**英文**：A subspace W of V is called T-invariant if T(W)⊆W. Equivalently, the restriction of T to W takes values in W.

**直译**：V 的一个子空间 W 被称为 T-不变的，如果 T(W)⊆W。等价地，T 在 W 上的限制取值于 W。

**改稿**：若 V 的子空间 W 满足 T(W)⊆W，则称 W 为 T-不变子空间。换言之，T 在 W 上的限制仍取值于 W。

**取舍**：条件与名称成一完整句，后句解释同一条件。若前文已在讨论“T-不变子空间”的定义，也可先写“称……为……，如果……”，没有固定优先式。

## E06：将性质展开为检验条件

**英文**：The elements a and b are algebraically independent over k. In other words, if P∈k[X,Y] satisfies P(a,b)=0, then P=0.

**直译**：元素 a 和 b 在 k 上是代数无关的。用其他话说，如果……

**改稿**：a 与 b 在 k 上代数无关。换言之，若 P∈k[X,Y] 满足 P(a,b)=0，则 P=0。

**取舍**：保留展开解释，不能以两句等价为由删除第二句；也不再增加“因此可以把它们视为两个自由变量”等未给出的说明。

## E07：剩余任务与归约各有所指

**英文**：We already know that f is injective. It remains to prove surjectivity. By Lemma 2.1, it suffices to show that the image contains every generator of N.

**直译**：我们已经知道 f 是单射。它剩下去证明满射性。由引理 2.1，它充分去展示像包含 N 的每个生成元。

**改稿**：已知 f 是单射，还需证明它是满射。由引理 2.1，只需证明 f 的像包含 N 的每个生成元。

**取舍**：“还需”标明进度，“只需”说明归约。若原书已指定一组生成元，中文可据该上下文写“上述各生成元”；不能凭空另选一组。

## E08：有两种证明，不是证明的两步

**英文**：There are two proofs of this assertion. The first uses the universal property. Alternatively, one can write down the inverse explicitly.

**直译**：这个断言有两个证明。第一个使用泛性质。进一步地，一个人可以显式地写下逆。

**改稿**：这一断言有两种证明：一种利用泛性质；另一种直接写出逆映射。

**取舍**：冒号和分号显出平行路线，改掉 alternatively 的误译。本例允许纠正明确衔接误译；若任务仅准标建议，应交此候选而不擅自写回。

## E09：构造后说明它完成的任务

**英文**：To prove surjectivity, take y∈N. Since q is surjective, choose x∈M with q(x)=y. Then g(x+K)=y, as required.

**直译**：为了证明满射性，取 y∈N。由于 q 是满射，选择有 q(x)=y 的 x∈M。然后 g(x+K)=y，如所要求的。

**改稿**：为证明满性，任取 y∈N。由 q 的满性，可取 x∈M 使 q(x)=y。于是 g(x+K)=y，所需原像已找到。

**取舍**：结尾解释 as required 在本段所指的任务；不称整条定理已经证明。使用前文定义的 g 与 q，不另改公式。若原文的 take 是特殊选取而非任意元素，则不能补“任取”。

## E10：保留相似论证中专门点出的差异

**英文**：The proof is the same as that of Proposition 3.2, except that we use injectivity of u in place of surjectivity of v.

**直译**：证明与命题 3.2 的那一个相同，除了我们使用 u 的单射性在 v 的满射性的位置。

**改稿**：证明与命题 3.2 类似，只需将其中用到 v 满性的地方改用 u 的单性。

**取舍**：原文的 same 受 except 限定，中文“类似”与后句共同表达。不能压成“同理可证”，否则丢掉此处明确指出的变化。

## E11：从存在同构转到同构的形式

**英文**：The two functors are left adjoint to the same functor and hence are naturally isomorphic. Explicitly, the component at M sends r⊗m to rm.

**直译**：两个函子是相同函子的左伴随并因此自然同构。显式地，在 M 处的分量把 r⊗m 送到 rm。

**改稿**：这两个函子同为一个函子的左伴随，因而自然同构。具体地，该自然同构在 M 处的分量将 r⊗m 映为 rm。

**取舍**：第二句解释已有同构，不重新宣布同构存在。本例假定前文已给出使该式有意义的模结构；不据此套用到任意张量积。

## E12：基选定后再转成矩阵语言

**英文**：Choose bases of V and W, and let A be the matrix of T in these bases. Under these identifications, the equation T(v)=w becomes Ax=b, where x and b are the coordinate vectors of v and w.

**直译**：选择 V 和 W 的基并让 A 是 T 在这些基中的矩阵。在这些识别下，等式……

**改稿**：选定 V 与 W 的基，记 T 在这两组基下的矩阵为 A。在上述识别下，T(v)=w 化为 Ax=b，其中 x、b 分别是 v、w 的坐标向量。

**取舍**：先保留基的选择，再说明表示转换；不能把 v 与 x、w 与 b 无条件当成原本相同的对象。

## E13：公式链与解释构成完整句群

**英文**：We have g(f(x))=h(x)=x, where the first equality follows from (2.4) and the second from the definition of h. Thus gf is the identity.

**直译**：我们有 g(f(x))=h(x)=x，在那里第一个等式跟随于 (2.4) 并且第二个跟随于 h 的定义。因此 gf 是恒等。

**改稿**：有 g(f(x))=h(x)=x，其中第一个等号由 (2.4) 得到，第二个等号由 h 的定义得到。因此 gf 为恒等映射。

**取舍**：保留各步依据及末句结论。TeX 中若公式采用显示环境，仍按这个句法连接，不更换标签或将公式重排成另一种形式。

## E14：定义之后解释选择无关性

**英文**：Define F(x)=f(y), where y is any lift of x. Lemma 1.4 shows that the right-hand side is independent of the choice of y.

**直译**：定义 F(x)=f(y)，其中 y 是 x 的任意提升。引理 1.4 展示右边是独立于 y 的选择的。

**改稿**：定义 F(x)=f(y)，其中 y 是 x 的任一提升。由引理 1.4，右端与 y 的选取无关。

**取舍**：不删第二句；它交代公式为何能够定义 F。也不改成“任意 y 都可以”，因为 y 必须是 x 的提升。

## E15：局部约定和临时搁置

**英文**：For the rest of this section, k is fixed while n may vary. For the moment, we disregard convergence and regard the series as formal.

**直译**：对于本节剩余的部分，k 被固定而 n 可以变化。对于这一时刻，我们忽视收敛并把级数认为是形式的。

**改稿**：本节以下固定 k，允许 n 变化。暂且不论收敛性，将该级数视为形式级数。

**取舍**：一个约定持续到节末，另一个只是暂时处理；不能合并为“以下所有级数均无需收敛”。

## E16：比较时保留共同对象与不同结论

**英文**：For a finite family, this map is an isomorphism. For an infinite family, however, it need not be surjective.

**直译**：对于一个有限族，这个映射是一个同构。然而，对于一个无限族，它不需要是满射。

**改稿**：对有限族，该映射是同构；对无限族，它却未必是满射。

**取舍**：两个分句共享“该映射”，对比落在族的有限性；not necessarily 不能译成一定不满。

## E17：分别配对过长时展开

**英文**：The maps u and v induce isomorphisms on the kernels and cokernels, respectively.

**直译**：映射 u 和 v 分别在核和余核上诱导同构。

**改稿**：u 在核上诱导同构，v 在余核上诱导同构。

**取舍**：原译并非错误；当上下文已有多组对象时，展开可以减少配对负担。对象简单且无歧义时保留原译即可，不能为了“润色”强行增加长度。

## E18：从已有结果接到下一任务

**英文**：We have defined the objects, but have not yet produced any nontrivial examples. The next section supplies such examples and studies their basic properties.

**直译**：我们已经定义了这些对象，但是尚未生产任何非平凡例子。下一节供应这样的例子并研究它们的基本性质。

**改稿**：我们已经定义了这些对象，但还没有给出非平凡的例子。下一节将给出这样的例子，并研究它们的基本性质。

**取舍**：重复“例子”能保持承接，不必为避免重复换成泛泛“内容”。不增加“填补理论空白”“展示深刻联系”等原文没有的评价。

## E19：保留作者邀请读者检验的语气

**英文**：It is instructive to check this identity directly. We leave this verification to the reader.

**直译**：直接检查这个恒等式是有教育意义的。我们把这一验证留给读者。

**改稿**：直接验证这一恒等式很有益。我们将这一步留给读者。

**取舍**：保留教材中的作者引导与省略身份，不自动补出计算，也不把它删成“显然”。原文若有承接前法的 also，可按上下文加“也”；本例没有，不主动添加。

## E20：长句拆分后保留全段假设

**英文**：Assume that M is finite-dimensional. Choose a basis of M; its images span N because f is surjective, so N is finite-dimensional as well.

**直译**：假定 M 是有限维的。选择 M 的一个基；它的像张成 N，因为 f 是满射，所以 N 也是有限维的。

**改稿**：假设 M 有限维，并取 M 的一组基。由于 f 是满射，这组基中各向量的像张成 N，故 N 也有限维。

**取舍**：用“各向量的像”明确“基的像”；共同假设仍支撑整个论证。默认 f 的线性等前提已经在例子的上下文中给出，不把片段推广为任意满射的结论。

## 自查方式

改稿至少同时通过两项检查：中文能否顺着对象与任务读下去；原英文的每项独立信息是否仍有对应。例中确有上下文依赖的位置已明示，不借例文补造源书条件。以上为作者自查用例，未经过独立模型盲测；结构校验工具不评价这些中文句子的优劣。
