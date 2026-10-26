#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdbool.h>
#include <limits.h>
typedef struct { int u, v, weight; } Edge;

bool repairMST(const int w[100][100], int V,
               const Edge mst[], int failedIndex,
               Edge *replacement, long long *newWeight) {
    bool inFirst[100] = {false};
    int stack[100], top = 0;
    int start = mst[failedIndex].u;
    inFirst[start] = true;
    stack[top++] = start;

    while (top > 0) {
        int u = stack[--top];
        for (int i = 0; i < V - 1; ++i) {
            if (i == failedIndex) continue;
            int v = -1;
            if (mst[i].u == u) v = mst[i].v;
            else if (mst[i].v == u) v = mst[i].u;
            if (v >= 0 && !inFirst[v]) {
                inFirst[v] = true;
                stack[top++] = v;
            }
        }
    }

    int best = INT_MAX;
    Edge chosen = {0, 0, 0};
    int a = mst[failedIndex].u, b = mst[failedIndex].v;
    for (int u = 0; u < V; ++u) {
        for (int v = u + 1; v < V; ++v) {
            if (inFirst[u] == inFirst[v]) continue;
            if ((u == a && v == b) || (u == b && v == a)) continue;
            if (w[u][v] != INT_MAX && w[u][v] < best) {
                best = w[u][v];
                chosen = (Edge){u, v, w[u][v]};
            }
        }
    }
    if (best == INT_MAX) return false;

    long long total = 0;
    for (int i = 0; i < V - 1; ++i) total += mst[i].weight;
    *replacement = chosen;
    *newWeight = total - mst[failedIndex].weight + best;
    return true;
}

static unsigned seed=67;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static int parent[100];
static int find(int x){while(parent[x]!=x)x=parent[x]=parent[parent[x]];return x;}
static int kruskal(const int w[100][100],int V,int banA,int banB,Edge out[100],long long *total){for(int i=0;i<V;i++)parent[i]=i;int n=0;*total=0;while(n<V-1){int best=INT_MAX,a=-1,b=-1;for(int u=0;u<V;u++)for(int v=u+1;v<V;v++){if((u==banA&&v==banB)||w[u][v]>=best||find(u)==find(v))continue;best=w[u][v];a=u;b=v;}if(a<0)return 0;out[n++]=(Edge){a,b,best};*total+=best;parent[find(a)]=find(b);}return 1;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  static int w[100][100];int V=2+rnd()%9;for(int i=0;i<V;i++)for(int j=0;j<V;j++)w[i][j]=(i==j?0:INT_MAX);
  for(int i=1;i<V;i++){int p=rnd()%i,v=rnd()%16;w[i][p]=w[p][i]=v;}
  for(int i=0;i<V;i++)for(int j=i+1;j<V;j++)if(w[i][j]==INT_MAX&&rnd()%3==0){int v=rnd()%16;w[i][j]=w[j][i]=v;}
  Edge old[100],oracleTree[100],rep={-1,-1,-1};long long oldWeight,newWeight=1234567,oracleWeight;assert(kruskal(w,V,-1,-1,old,&oldWeight));int failed=rnd()%(V-1),a=old[failed].u,b=old[failed].v;
  int expected=kruskal(w,V,a,b,oracleTree,&oracleWeight);int got=repairMST(w,V,old,failed,&rep,&newWeight);assert(got==expected);
  if(!got){assert(rep.u==-1&&rep.v==-1&&rep.weight==-1&&newWeight==1234567);}else{
   assert(rep.u>=0&&rep.v>=0&&rep.u<V&&rep.v<V&&rep.u!=rep.v&&w[rep.u][rep.v]==rep.weight);assert(!((rep.u==a&&rep.v==b)||(rep.u==b&&rep.v==a)));assert(newWeight==oracleWeight);
   for(int i=0;i<V;i++){parent[i]=i;}
   for(int i=0;i<V-1;i++){
    if(i!=failed){assert(find(old[i].u)!=find(old[i].v));parent[find(old[i].u)]=find(old[i].v);}
   }
   assert(find(rep.u)!=find(rep.v));parent[find(rep.u)]=find(rep.v);
   for(int i=1;i<V;i++){assert(find(i)==find(0));}
  }
 }
 puts("S4-IV03 1000 random MST edge failures OK");return 0;
}
