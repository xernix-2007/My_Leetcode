class Solution {
public:
    bool rotateString(string s, string goal) {
        if (s.length() != goal.length())
            return false;
        string x = s + s;
        return x.find(goal) != string::npos;
    }
};