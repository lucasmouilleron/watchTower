public class test
{
    ////////////////////////////////////////////////////////////////////////////////
    public static final int PORT = 4443;
    public static final String URL = "https://localhost.com";
    public static final String PASSWORD = "change me";
    public static final String ALERT_TYPE = "pushover";
    public static final String ALERT_TARGET = "pushoverTargetID";
    public static final boolean ALLOW_UNSAFE_HTTPS = true;


    ////////////////////////////////////////////////////////////////////////////////
    public static void main(String[] args)
    {
        try
        {
            client client = new client(URL, PORT, PASSWORD, ALLOW_UNSAFE_HTTPS);
            String content = client.pulse("testJava", ALERT_TYPE, ALERT_TARGET, 60);
            System.out.println(content);
            client.cancel("testJava");
            client.add("testJava","ok message",3, false);
        }
        catch(Exception e)
        {
            e.printStackTrace();
        }
    }
}
