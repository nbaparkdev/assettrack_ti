package service

import "testing"

func TestParseNFEXML_WithNFeProcWrapper(t *testing.T) {
	xmlData := []byte(`<?xml version="1.0" encoding="UTF-8"?>
<nfeProc xmlns="http://portalfiscal.inf.br" versao="4.00">
  <NFe>
    <infNFe versao="4.00" Id="NFe35260899999999999999550010000000011000000000">
      <ide>
        <natOp>Venda de mercadoria</natOp>
        <nNF>1</nNF>
        <dhEmi>2026-08-19T18:00:00-03:00</dhEmi>
      </ide>
      <emit>
        <CNPJ>99999999999999</CNPJ>
        <xNome>Razao Social do Emitente LTDA</xNome>
        <enderEmit>
          <xlgr>Av Paulista</xlgr>
          <n>1000</n>
          <xBairro>Bela Vista</xBairro>
          <xMun>Sao Paulo</xMun>
          <UF>SP</UF>
        </enderEmit>
      </emit>
      <dest>
        <CNPJ>88888888888888</CNPJ>
        <xNome>Razao Social do Destinatario SA</xNome>
      </dest>
      <det nItem="1">
        <prod>
          <cProd>PROD001</cProd>
          <xProd>Produto Exemplo Modelo NF-e</xProd>
          <NCM>21069090</NCM>
          <qCom>1.0000</qCom>
          <vUnCom>100.0000</vUnCom>
          <vProd>100.00</vProd>
        </prod>
      </det>
      <total>
        <ICMSTot>
          <vNF>100.00</vNF>
        </ICMSTot>
      </total>
    </infNFe>
  </NFe>
</nfeProc>`)

	parsed, err := ParseNFEXML(xmlData)
	if err != nil {
		t.Fatalf("expected XML to parse, got error: %v", err)
	}

	if parsed.NumeroNota != "1" {
		t.Fatalf("expected NumeroNota=1, got %q", parsed.NumeroNota)
	}
	if parsed.EmitenteNome != "Razao Social do Emitente LTDA" {
		t.Fatalf("unexpected EmitenteNome: %q", parsed.EmitenteNome)
	}
	if parsed.EmitenteCNPJ != "99999999999999" {
		t.Fatalf("unexpected EmitenteCNPJ: %q", parsed.EmitenteCNPJ)
	}
	if parsed.EmitenteEndereco != "Av Paulista, 1000, Bela Vista" {
		t.Fatalf("unexpected EmitenteEndereco: %q", parsed.EmitenteEndereco)
	}
	if parsed.EmitenteCidade != "Sao Paulo" {
		t.Fatalf("unexpected EmitenteCidade: %q", parsed.EmitenteCidade)
	}
	if parsed.EmitenteEstado != "SP" {
		t.Fatalf("unexpected EmitenteEstado: %q", parsed.EmitenteEstado)
	}
	if len(parsed.Itens) != 1 {
		t.Fatalf("expected 1 item, got %d", len(parsed.Itens))
	}
}
