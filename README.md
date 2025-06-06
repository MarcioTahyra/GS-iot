# Sistema de Reconhecimento de Gestos em Situações de Apagão

### Autores  
- **Vinícius Almeida Bernardino de Souza** – 97888  
- **Jessica Witzler Costacurta** – 99068  
- **Márcio Hitoshi Tahyra** – 552511  

---

## O Problema

A falta de energia elétrica pode gerar situações críticas em diversos contextos, desde lares comuns até hospitais.

Durante apagões, a visibilidade é comprometida, dificultando a comunicação, a movimentação e o acionamento de alertas em tempo hábil.  
Pessoas com mobilidade reduzida ou deficiência visual enfrentam riscos ainda maiores, como quedas, desorientação e dificuldade de solicitar ajuda.

**Portanto, há uma necessidade clara de soluções acessíveis**, que não dependam de infraestrutura complexa, e que funcionem com recursos mínimos, como uma câmera comum e um computador — para oferecer suporte inteligente durante apagões.

---

## A Solução

Desenvolvemos uma **aplicação em Python** utilizando a biblioteca **MediaPipe** para **reconhecimento de gestos corporais específicos**, mesmo em ambientes com pouca ou nenhuma iluminação.

- Gestos podem ser **cadastrados previamente**, assim como a **mensagem associada a cada gesto**.
- Ideal para uso com **câmeras de visão noturna** ou vídeos com **iluminação mínima**, simulando cenários reais de apagão.

---

## Como Usar

### 1º Passo: Cadastrar Poses e Mensagens
- **Arraste e solte** os pontos azuis para salvar as poses desejadas.
- Associe uma **mensagem personalizada** a cada gesto salvo.

![image](https://github.com/user-attachments/assets/4c657f7d-5c7f-4b32-9cd0-d9e5af7371cd)

---

###  2º Passo: Rodar o Identificador de Poses
- Execute o sistema de reconhecimento.
- Ajuste a **Tolerância** usando o **slider** conforme necessário para maior precisão.

![image](https://github.com/user-attachments/assets/531ae9df-4e38-4835-8b9c-d6dafad470fe)

---

### 3º Passo: Monitoramento via WebSocket
- Acesse: [HiveMQ WebSocket Client](https://www.hivemq.com/demos/websocket-client/)
- Inscreva-se no tópico: `GS/3ESA/iot` para receber as mensagens dos gestos detectados.

![image](https://github.com/user-attachments/assets/f7484a2c-4713-451a-b6e2-fbbe47b156c6)
