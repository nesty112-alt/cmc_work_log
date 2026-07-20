import com.woongjin.app.lineworks.client.WorksApiMessageClient;
import com.woongjin.app.lineworks.client.model.SendMessageRequest;
import com.woongjin.app.lineworks.client.model.WorksApiResult;

import java.util.HashMap;
import java.util.Map;
import java.util.Arrays;

public class NaverWorksSender {
    public static void main(String[] args) {
        if (args.length < 5) {
            System.err.println("Usage: java NaverWorksSender <apiBaseUrl> <secretKey> <botId> <email> <reportUrl>");
            System.exit(1);
        }
        String apiBaseUrl = args[0];
        String secretKey = args[1];
        int botId = Integer.parseInt(args[2]);
        String email = args[3];
        String reportUrl = args[4];
        
        WorksApiMessageClient client = new WorksApiMessageClient(apiBaseUrl, secretKey);
        
        Map<String, Object> content = new HashMap<>();
        content.put("contentText", "금일 재원점검·퇴원분석 업무일지가 갱신되었습니다. 아래 링크를 확인하세요.");
        content.put("linkText", "생성된 보고서(대시보드) 열기");
        content.put("link", reportUrl);
        
        SendMessageRequest request = new SendMessageRequest(
            botId,
            "link",
            "user",
            Arrays.asList(email),
            content
        );
        
        try {
            WorksApiResult result = client.sendMessage(request);
            // Result code in the API might vary, but usually printing it helps
            System.out.println("Result code: " + result.getCode() + ", message: " + result.getMessage());
        } catch (Exception e) {
            e.printStackTrace();
            System.exit(1);
        }
    }
}
