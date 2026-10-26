#include <stddef.h>
#include <stdlib.h>
typedef struct Arc { int to; struct Arc *next; } Arc;
typedef struct Graph { int V; Arc **head; } Graph;
typedef enum { ORDER_OK, REORDER, CYCLE } State;

State classifyArc(const Graph *G, const int sigma[], int u, int v) {
    if (u == v) return CYCLE;
    int V = G->V;
    int *pos = malloc((size_t)V * sizeof *pos);
    if (pos == NULL) abort();
    for (int i = 0; i < V; ++i) pos[sigma[i]] = i;
    if (pos[u] < pos[v]) {
        free(pos);
        return ORDER_OK;
    }
    free(pos);

    unsigned char *seen = calloc((size_t)V, sizeof *seen);
    int *stack = malloc((size_t)V * sizeof *stack);
    if (seen == NULL || stack == NULL) {
        free(seen);
        free(stack);
        abort();
    }
    int top = 0;
    stack[top++] = v;
    seen[v] = 1;
    while (top != 0) {
        int x = stack[--top];
        if (x == u) {
            free(seen);
            free(stack);
            return CYCLE;
        }
        for (const Arc *e = G->head[x]; e != NULL; e = e->next) {
            int y = e->to;
            if (!seen[y]) {
                seen[y] = 1;
                stack[top++] = y;
            }
        }
    }
    free(seen);
    free(stack);
    return REORDER;
}

#include <assert.h>
#include <stdio.h>
static unsigned r=9829u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static int path(int n,unsigned char a[9][9],int src,int dst){int seen[9]={0},q[9],l=0,h=0;q[h++]=src;seen[src]=1;while(l<h){int x=q[l++];if(x==dst)return 1;for(int y=0;y<n;y++)if(a[x][y]&&!seen[y]){seen[y]=1;q[h++]=y;}}return 0;}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=1+(int)(rng()%9),ord[9],pos[9];unsigned char mat[9][9]={{0}};Arc *head[9]={0};Graph g={n,head};
    for(int i=0;i<n;i++)ord[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=ord[i];ord[i]=ord[j];ord[j]=t;}
    for(int i=0;i<n;i++)pos[ord[i]]=i;
    for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rng()%4==0){int a=ord[i],b=ord[j];mat[a][b]=1;Arc *e=malloc(sizeof *e);assert(e);e->to=b;e->next=head[a];head[a]=e;}
    int u=(int)(rng()%(unsigned)n),v=(int)(rng()%(unsigned)n);
    if(u!=v && mat[u][v]){trial--;for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}continue;}
    State want=(u==v || path(n,mat,v,u))?CYCLE:((pos[u]<pos[v])?ORDER_OK:REORDER);
    assert(classifyArc(&g,ord,u,v)==want);
    for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}
  }
  puts("S6-IV03 PASS 5000 random DAG/new-arc cases");return 0;
}