#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <limits.h>
#include <stdbool.h>

static int countDfs(const int g[12][12], int V, int u, int t,
                    int usedEdges, int k, bool onPath[12]) {
    if (usedEdges == k) return u == t ? 1 : 0;
    if (u == t) return 0;
    int ans = 0;
    for (int v = 0; v < V; ++v) {
        if (g[u][v] && !onPath[v]) {
            onPath[v] = true;
            ans += countDfs(g, V, v, t, usedEdges + 1, k, onPath);
            onPath[v] = false;
        }
    }
    return ans;
}

int countPaths(const int g[12][12], int V, int s, int t, int k) {
    bool onPath[12] = {false};
    onPath[s] = true;
    return countDfs(g, V, s, t, 0, k, onPath);
}

static unsigned seed=29;
static unsigned rnd(void){seed=seed*1664525u+1013904223u;return seed;}
static int oracle(const int g[12][12],int V,int u,int t,int left,int mask){if(left==0)return u==t;if(u==t)return 0;int ans=0;for(int v=0;v<V;v++)if(g[u][v]&&!(mask&(1<<v)))ans+=oracle(g,V,v,t,left-1,mask|(1<<v));return ans;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  int g[12][12]={{0}},V=1+rnd()%8;for(int u=0;u<V;u++)for(int v=u+1;v<V;v++){g[u][v]=g[v][u]=rnd()%3==0;}
  for(int s=0;s<V;s++)for(int t=0;t<V;t++)for(int k=0;k<V;k++){int got=countPaths(g,V,s,t,k),want=oracle(g,V,s,t,k,1<<s);assert(got==want);}
 }
 puts("S3-IV03 1000 random graphs, all s/t/k OK");return 0;
}
