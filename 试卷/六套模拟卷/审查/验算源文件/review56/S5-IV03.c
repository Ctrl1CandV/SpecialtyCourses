#include <stddef.h>
typedef struct Node { struct Node *left, *right; } Node;

static int heightAndUpdate(const Node *p, int *best) {
    if (p == NULL) return -1;
    int left = heightAndUpdate(p->left, best);
    int right = heightAndUpdate(p->right, best);
    int through = left + right + 2;
    if (through > *best) *best = through;
    return (left > right ? left : right) + 1;
}

int treeDiameter(const Node *root) {
    int best = 0;
    heightAndUpdate(root, &best);
    return best;
}

#include <assert.h>
#include <stdio.h>
static unsigned r=4973u;
static unsigned rng(void){r=r*1664525u+1013904223u;return r;}
int main(void){
  for(int trial=0;trial<5000;trial++){
    int n=(int)(rng()%20);Node a[20];int adj[20][20]={{0}};
    for(int i=0;i<n;i++)a[i].left=a[i].right=NULL;
    for(int i=1;i<n;i++){
      int p;do{p=(int)(rng()%(unsigned)i);}while(a[p].left&&a[p].right);
      if(!a[p].left && (!a[p].right || rng()%2==0))a[p].left=&a[i];else a[p].right=&a[i];
      adj[i][p]=adj[p][i]=1;
    }
    int expect=0;
    for(int src=0;src<n;src++){
      int dist[20],queue[20],head=0,tail=0;for(int j=0;j<n;j++)dist[j]=-1;
      dist[src]=0;queue[tail++]=src;
      while(head<tail){int x=queue[head++];for(int y=0;y<n;y++)if(adj[x][y]&&dist[y]<0){dist[y]=dist[x]+1;queue[tail++]=y;}}
      for(int j=0;j<n;j++)if(dist[j]>expect)expect=dist[j];
    }
    assert(treeDiameter(n?&a[0]:NULL)==expect);
  }
  puts("S5-IV03 PASS 5000 random trees vs all-pairs BFS");return 0;
}