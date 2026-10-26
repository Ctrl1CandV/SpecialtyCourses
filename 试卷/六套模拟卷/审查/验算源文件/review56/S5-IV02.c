#include <stdbool.h>
#include <stddef.h>
#include <stdlib.h>
typedef struct Arc { int to; struct Arc *next; } Arc;
typedef struct Graph { int V; Arc **head; } Graph;

bool canBePrefix(const Graph *G, const int P[], int k) {
    if (k == 0) return true;
    int *indeg = calloc((size_t)G->V, sizeof *indeg);
    if (indeg == NULL) abort();
    for (int u = 0; u < G->V; ++u)
        for (const Arc *e = G->head[u]; e != NULL; e = e->next)
            ++indeg[e->to];
    for (int i = 0; i < k; ++i) {
        int u = P[i];
        if (indeg[u] != 0) {
            free(indeg);
            return false;
        }
        for (const Arc *e = G->head[u]; e != NULL; e = e->next)
            --indeg[e->to];
    }
    free(indeg);
    return true;
}

#include <assert.h>
#include <stdio.h>
static unsigned r=2871u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
static int predcheck(int n, unsigned char arc[8][8], const int p[],int k){
  int used[8]={0};for(int i=0;i<k;i++){int u=p[i];for(int a=0;a<n;a++)if(arc[a][u]&&!used[a])return 0;used[u]=1;}return 1;
}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=1+(int)(rng()%8),ord[8],p[8];unsigned char mat[8][8]={{0}};Arc *head[8]={0};Graph g={n,head};
    for(int i=0;i<n;i++)ord[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=ord[i];ord[i]=ord[j];ord[j]=t;}
    for(int i=0;i<n;i++)for(int j=i+1;j<n;j++)if(rng()%3==0){int a=ord[i],b=ord[j];mat[a][b]=1;Arc *e=malloc(sizeof *e);assert(e);e->to=b;e->next=head[a];head[a]=e;}
    for(int i=0;i<n;i++)p[i]=i;
    for(int i=n-1;i>0;i--){int j=(int)(rng()%(unsigned)(i+1));int t=p[i];p[i]=p[j];p[j]=t;}
    int k=(int)(rng()%(unsigned)(n+1));
    assert(canBePrefix(&g,p,k)==predcheck(n,mat,p,k));
    for(int a=0;a<n;a++){Arc *e=head[a];while(e){Arc *next=e->next;free(e);e=next;}}
  }
  puts("S5-IV02 PASS 5000 random DAG/prefix cases");return 0;
}