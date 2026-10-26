#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
typedef struct Arc {
    int to;
    struct Arc *next;
} Arc;
typedef struct {
    int V, E;
    Arc **head;
} Graph;

static int dfsAvoid(const Graph *G, int u, int t, int w,
                    unsigned char seen[100], int path[],
                    int depth, int *pathLen) {
    seen[u] = 1;
    path[depth] = u;
    if (u == t) {
        *pathLen = depth + 1;
        return 1;
    }
    for (const Arc *e = G->head[u]; e != 0; e = e->next) {
        int v = e->to;
        if (v != w && !seen[v] &&
            dfsAvoid(G, v, t, w, seen, path, depth + 1, pathLen))
            return 1;
    }
    return 0;
}

int pathAvoidingVertex(const Graph *G, int s, int t, int w,
                       int *path, int *pathLen) {
    unsigned char seen[100] = {0};
    *pathLen = 0;
    return dfsAvoid(G, s, t, w, seen, path, 0, pathLen);
}

static unsigned z=43;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static void edge(Graph *g,int u,int v){Arc *a=malloc(sizeof(Arc)),*b=malloc(sizeof(Arc));a->to=v;a->next=g->head[u];g->head[u]=a;b->to=u;b->next=g->head[v];g->head[v]=b;g->E++;}
static void clear(Graph *g){for(int i=0;i<g->V;i++){Arc *p=g->head[i];while(p){Arc *q=p->next;free(p);p=q;}}free(g->head);}
static int adjacent(const Graph *g,int u,int v){for(Arc *p=g->head[u];p;p=p->next)if(p->to==v)return 1;return 0;}

static int ref(const Graph *g,int s,int t,int w){int q[100],seen[100]={0},h=0,r=0;seen[w]=seen[s]=1;q[r++]=s;while(h<r){int u=q[h++];if(u==t)return 1;for(Arc *a=g->head[u];a;a=a->next)if(!seen[a->to]){seen[a->to]=1;q[r++]=a->to;}}return 0;}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Graph g;g.V=3+rnd()%27;g.E=0;g.head=calloc(g.V,sizeof(Arc*));for(int u=0;u<g.V;u++)for(int v=u+1;v<g.V;v++)if(rnd()%6==0)edge(&g,u,v);
  int s=rnd()%g.V,t=rnd()%g.V,w=rnd()%g.V;while(t==s)t=(t+1)%g.V;while(w==s||w==t)w=(w+1)%g.V;
  int path[100],len=-1,got=pathAvoidingVertex(&g,s,t,w,path,&len),want=ref(&g,s,t,w);assert(got==want);if(!got)assert(len==0);else{int seen[100]={0};assert(len>=2&&len<=g.V&&path[0]==s&&path[len-1]==t);for(int i=0;i<len;i++){assert(path[i]!=w&&!seen[path[i]]);seen[path[i]]=1;if(i)assert(adjacent(&g,path[i-1],path[i]));}}
  clear(&g);
 }
 puts("S1-IV03 OK 1000 random graphs");return 0;
}
