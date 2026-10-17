import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Text } from "@/components/ui/text";
import { View } from "react-native";

export default function Index() {
  return (
    <View className="flex-1 items-center justify-center bg-background p-6">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <Badge variant="secondary" className="self-start">
            <Text>Café Demo</Text>
          </Badge>
          <CardTitle className="mt-2">Mesa7</CardTitle>
          <CardDescription>Pide desde tu celular y sigue tu pedido en vivo.</CardDescription>
        </CardHeader>
        <CardContent>
          <Button>
            <Text>Empezar</Text>
          </Button>
        </CardContent>
      </Card>
    </View>
  );
}
