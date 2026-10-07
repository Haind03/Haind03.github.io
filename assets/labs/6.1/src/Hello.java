public class Hello {
    static int add(int a, int b) {
        return a + b;
    }

    static boolean checkPass(String s) {
        return s.length() == 8 && s.equals("JavaRev!");
    }

    public static void main(String[] args) {
        int x = add(3, 4);
        System.out.println("x = " + x);
        if (checkPass("JavaRev!")) {
            System.out.println("Correct!");
        } else {
            System.out.println("Wrong");
        }
    }
}
