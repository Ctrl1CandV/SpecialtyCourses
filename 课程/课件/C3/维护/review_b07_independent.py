"""独立读取 B07 现行讲稿代码，核验删除结果及表达式语法树语义。

仅在 _tmp/c3_revision/b07_independent 中写入编译和运行中间文件。
参考结果来自逐项过滤及独立表达式解析器，不复用作者测试。
"""
from pathlib import Path
import os
import re
import shutil
import subprocess

ROOT = Path(__file__).resolve().parents[4]
LESSON = ROOT / '课程/课件/C3/C3-B-07'
WORK = ROOT / '_tmp/c3_revision/b07_independent'
GXX = os.environ.get('C3_GXX') or os.environ.get('CXX') or shutil.which('g++') or 'D:/Program Files/mingw64/bin/g++.exe'


def before_main(code):
    return code[:code.index('int main()')]


def compile_run(name, code):
    src = WORK / f'{name}.cpp'
    exe = WORK / f'{name}.exe'
    src.write_text(code, encoding='utf-8')
    subprocess.run([GXX, '-std=c++17', '-O2', '-Wall', '-Wextra', '-Werror',
                    '-pedantic', str(src), '-o', str(exe)], check=True)
    return subprocess.check_output([str(exe)], text=True, encoding='utf-8').strip()


def main():
    WORK.mkdir(parents=True, exist_ok=True)
    md = (LESSON / 'C3-B-07-讲稿.md').read_text(encoding='utf-8')
    code = re.findall(r'```cpp\n(.*?)\n```', md, re.S)
    assert len(code) == 2
    assert compile_run('original_delete', code[0]) == '-3 -1 9'
    assert compile_run('original_expression', code[1]) == '(a*b)+(-(c-d))'

    delete_harness = r'''
#include <vector>
#include <algorithm>
#include <functional>
#include <random>
#include <climits>
#include <iostream>
int main() {
    long long cases=0;
    auto check=[&](const std::vector<int> &a,int x,int y) {
        std::vector<int> storage(a.size()+2, 123456789);
        std::copy(a.begin(),a.end(),storage.begin()+1);
        std::vector<int> expected;
        for(int v:a) if(x>y || v<x || v>y) expected.push_back(v);
        int n=(int)a.size();
        int removed=DeleteRange(storage.data()+1,&n,x,y);
        assert(n==(int)expected.size());
        assert(removed==(int)a.size()-n);
        assert(std::equal(expected.begin(),expected.end(),storage.begin()+1));
        assert(storage.front()==123456789 && storage.back()==123456789);
        ++cases;
    };
    for(int n=0;n<=9;++n) {
        std::vector<int>a(n);
        std::function<void(int,int)> enumerate=[&](int pos,int minv) {
            if(pos==n) {
                for(int x=-3;x<=3;++x) for(int y=-3;y<=3;++y) check(a,x,y);
                return;
            }
            for(int v=minv;v<=2;++v) { a[pos]=v; enumerate(pos+1,v); }
        };
        enumerate(0,-2);
    }
    std::mt19937 rng(8020701);
    for(int run=0;run<10000;++run) {
        std::vector<int>a(run%121);
        for(int &v:a) v=(int)(rng()%1001)-500;
        if(a.size()>2 && run%7==0) { a.front()=INT_MIN; a.back()=INT_MAX; }
        std::sort(a.begin(),a.end());
        int x=(int)(rng()%1201)-600, y=(int)(rng()%1201)-600;
        check(a,x,y);
        check(a,INT_MIN,INT_MAX);
        check(a,INT_MIN,INT_MIN);
        check(a,INT_MAX,INT_MAX);
    }
    std::cout << "DeleteRange independent cases: " << cases << '\n';
}
'''
    print(compile_run('delete_independent', before_main(code[0]) + delete_harness))

    expression_prelude = r'''
#include <cstdio>
#include <cstddef>
#include <cassert>
#include <cstring>
#include <string>
#include <vector>
#include <memory>
#include <random>
#include <cctype>
#include <iostream>
std::string output;
void record(const char *s) { output += s; }
void record(const char *, const char *s) { output += s; }
'''
    expression_harness = r'''
// Independent parser: turn printed infix into postfix tokens with explicit arity.
struct Parser {
    const std::string &s;
    std::size_t pos=0;
    std::vector<std::string> tokens;
    void expr() {
        term();
        while(pos<s.size() && (s[pos]=='+' || s[pos]=='-')) {
            char op=s[pos++]; term(); tokens.push_back(std::string(1,op));
        }
    }
    void term() {
        unary();
        while(pos<s.size() && (s[pos]=='*' || s[pos]=='/')) {
            char op=s[pos++]; unary(); tokens.push_back(std::string(1,op));
        }
    }
    void unary() {
        if(pos<s.size() && s[pos]=='-') { ++pos; unary(); tokens.push_back("u-"); }
        else atom();
    }
    void atom() {
        assert(pos<s.size());
        if(s[pos]=='(') {
            ++pos; expr(); assert(pos<s.size() && s[pos]==')'); ++pos;
        } else {
            std::size_t start=pos;
            while(pos<s.size() && (std::isalnum((unsigned char)s[pos]) || s[pos]=='_')) ++pos;
            assert(pos>start); tokens.push_back(s.substr(start,pos-start));
        }
    }
};
// Expected semantics: iterative postorder with explicit visit flags.
std::vector<std::string> treeTokens(const BTree *root) {
    std::vector<std::string> result;
    std::vector<std::pair<const BTree*,bool>> work;
    if(root) work.push_back({root,false});
    while(!work.empty()) {
        auto item=work.back(); work.pop_back();
        auto t=item.first;
        if(item.second) {
            result.push_back((t->left==NULL) != (t->right==NULL) ? "u-" : std::string(t->data));
        } else {
            work.push_back({t,true});
            if(t->right) work.push_back({t->right,false});
            if(t->left) work.push_back({t->left,false});
        }
    }
    return result;
}
int main() {
    long long cases=0;
    auto check=[&](const BTree *root) {
        output.clear(); Infix(root);
        if(root==NULL) assert(output.empty());
        else {
            Parser p{output,0,{}}; p.expr(); assert(p.pos==output.size());
            assert(p.tokens==treeTokens(root));
        }
        ++cases;
    };
    check(NULL);
    BTree leaf={"abcdefghi",NULL,NULL}; check(&leaf);
    BTree unaryLeft={"-",&leaf,NULL}, unaryRight={"-",NULL,&leaf};
    check(&unaryLeft); check(&unaryRight);
    BTree nestedLeft={"-",&unaryLeft,NULL},nestedRight={"-",NULL,&unaryRight};
    check(&nestedLeft);check(&nestedRight);
    BTree zero={"0",NULL,NULL}, multichar={"123456789",NULL,NULL};
    BTree root={"-",&zero,&multichar};check(&root);
    std::mt19937 rng(8020702);
    const char *operands[]={"a","x2","var_1","0","12","123456789"};
    const char *ops[]={"+","-","*","/"};
    for(int run=0;run<25000;++run) {
        std::vector<std::unique_ptr<BTree>> owned;
        auto make=[&](const char *data, BTree *l, BTree *r) {
            owned.push_back(std::make_unique<BTree>());
            BTree *p=owned.back().get();
            std::strcpy(p->data,data);p->left=l;p->right=r;return p;
        };
        auto build=[&](auto &&self,int depth)->BTree* {
            if(depth==0 || rng()%4==0) return make(operands[rng()%6],NULL,NULL);
            if(rng()%3==0) {
                BTree *child=self(self,depth-1);
                return rng()%2 ? make("-",child,NULL) : make("-",NULL,child);
            }
            BTree *l=self(self,depth-1),*r=self(self,depth-1);
            return make(ops[rng()%4],l,r);
        };
        check(build(build,1+run%7));
    }
    std::cout << "Expression independent syntax/arity cases: " << cases << '\n';
}
'''
    expr_source = before_main(code[1]).replace('printf(', 'record(')
    print(compile_run('expression_independent', expression_prelude + expr_source + expression_harness))
    print('B07 independent verification passed; original example outputs also match.')


if __name__ == '__main__':
    main()
