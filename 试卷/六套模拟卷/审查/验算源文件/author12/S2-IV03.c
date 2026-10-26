#include <stdio.h>
#include <stdlib.h>
#include <assert.h>
#include <string.h>
#include <stddef.h>
typedef struct Arc {
    int to;
    struct Arc *next;
} Arc;
typedef struct {
    int V, E;
    Arc **head;
} Graph;

int pathAtMostK(const Graph *G, int s, int t, int k,
                int *path, int *pathLen) {
    *pathLen = 0;
    if (k < 0) return 0;
    if (s == t) {
        path[0] = s;
        *pathLen = 1;
        return 1;
    }

    int dist[100], parent[100], queue[100], rev[100];
    for (int i = 0; i < G->V; ++i) {
        dist[i] = -1;
        parent[i] = -1;
    }
    int front = 0, rear = 0;
    dist[s] = 0;
    queue[rear++] = s;
    while (front < rear && dist[t] == -1) {
        int u = queue[front++];
        for (const Arc *a = G->head[u]; a != NULL; a = a->next) {
            int v = a->to;
            if (dist[v] != -1) continue;
            dist[v] = dist[u] + 1;
            parent[v] = u;
            queue[rear++] = v;
        }
    }
    if (dist[t] == -1 || dist[t] > k) return 0;

    int len = 0;
    for (int v = t; v != -1; v = parent[v]) rev[len++] = v;
    for (int i = 0; i < len; ++i) path[i] = rev[len - 1 - i];
    *pathLen = len;
    return 1;
}

static unsigned z=43;
static unsigned rnd(void){z=z*1664525u+1013904223u;return z;}
static void edge(Graph *g,int u,int v){Arc *a=malloc(sizeof(Arc)),*b=malloc(sizeof(Arc));a->to=v;a->next=g->head[u];g->head[u]=a;b->to=u;b->next=g->head[v];g->head[v]=b;g->E++;}
static void clear(Graph *g){for(int i=0;i<g->V;i++){Arc *p=g->head[i];while(p){Arc *q=p->next;free(p);p=q;}}free(g->head);}
static int adjacent(const Graph *g,int u,int v){for(Arc *p=g->head[u];p;p=p->next)if(p->to==v)return 1;return 0;}

static int ref(const Graph *g,int s,int t){int q[100],d[100],h=0,r=0;for(int i=0;i<g->V;i++)d[i]=-1;d[s]=0;q[r++]=s;while(h<r){int u=q[h++];for(Arc *a=g->head[u];a;a=a->next)if(d[a->to]==-1){d[a->to]=d[u]+1;q[r++]=a->to;}}return d[t];}
int main(void){
 for(int tc=0;tc<1000;tc++){
  Graph g;g.V=1+rnd()%29;g.E=0;g.head=calloc(g.V,sizeof(Arc*));for(int u=0;u<g.V;u++)for(int v=u+1;v<g.V;v++)if(rnd()%5==0)edge(&g,u,v);
  int s=rnd()%g.V,t=rnd()%g.V,k=(int)(rnd()%(g.V+3))-1,path[100],len=-1;
  int got=pathAtMostK(&g,s,t,k,path,&len),d=ref(&g,s,t),want=k>=0&&d>=0&&d<=k;assert(got==want);
  if(!got)assert(len==0);else{int seen[100]={0};assert(path[0]==s&&path[len-1]==t&&len-1==d&&len-1<=k);for(int i=0;i<len;i++){assert(!seen[path[i]]);seen[path[i]]=1;if(i)assert(adjacent(&g,path[i-1],path[i]));}}
  clear(&g);
 }
 puts("S2-IV03 OK 1000 random graphs");return 0;
}
