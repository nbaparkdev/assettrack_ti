package service

import (
	"encoding/xml"
	"fmt"
	"strconv"
	"strings"
	"time"
)

// NFEXMLItem represents a product item extracted from an NFe XML.
type NFEXMLItem struct {
	Codigo        string   `json:"codigo"`
	Descricao     string   `json:"descricao"`
	NCM           string   `json:"ncm"`
	Quantidade    *float64 `json:"quantidade"`
	ValorUnitario *float64 `json:"valor_unitario"`
	ValorTotal    *float64 `json:"valor_total"`
}

// NFEData holds the extracted data from an NFe XML.
type NFEData struct {
	NumeroNota       string       `json:"numero_nota"`
	DataEmissao      *time.Time   `json:"data_emissao"`
	NaturezaOperacao string       `json:"natureza_operacao"`
	ValorTotal       *float64     `json:"valor_total"`
	EmitenteNome     string       `json:"emitente_nome"`
	EmitenteCNPJ     string       `json:"emitente_cnpj"`
	EmitenteEndereco string       `json:"emitente_endereco"`
	EmitenteCidade   string       `json:"emitente_cidade"`
	EmitenteEstado   string       `json:"emitente_estado"`
	EmitenteTelefone string       `json:"emitente_telefone"`
	DestinatarioNome string       `json:"destinatario_nome"`
	DestinatarioCNPJ string       `json:"destinatario_cnpj"`
	Itens            []NFEXMLItem `json:"itens"`
}

// Internal XML structs (Go matches elements by local name, ignoring namespaces)
type nfeXML struct {
	InfNFe nfeInfNFeXML `xml:"infNFe"`
}

type nfeInfNFeXML struct {
	Ide   nfeIdeXML   `xml:"ide"`
	Emit  nfeEmitXML  `xml:"emit"`
	Dest  nfeDestXML  `xml:"dest"`
	Total nfeTotalXML `xml:"total"`
	Dets  []nfeDetXML `xml:"det"`
}

type nfeIdeXML struct {
	NNF   string `xml:"nNF"`
	DhEmi string `xml:"dhEmi"`
	NatOp string `xml:"natOp"`
}

type nfeEmitXML struct {
	XNome     string      `xml:"xNome"`
	CNPJ      string      `xml:"CNPJ"`
	EnderEmit nfeEnderXML `xml:"enderEmit"`
}

type nfeEnderXML struct {
	XLgr    string `xml:"xLgr"`
	Nro     string `xml:"nro"`
	XBairro string `xml:"xBairro"`
	XMun    string `xml:"xMun"`
	UF      string `xml:"UF"`
	Fone    string `xml:"fone"`
}

type nfeDestXML struct {
	XNome string `xml:"xNome"`
	CNPJ  string `xml:"CNPJ"`
}

type nfeTotalXML struct {
	ICMSTot nfeICMSTotXML `xml:"ICMSTot"`
}

type nfeICMSTotXML struct {
	VNF string `xml:"vNF"`
}

type nfeDetXML struct {
	Prod nfeProdXML `xml:"prod"`
}

type nfeProdXML struct {
	CProd  string `xml:"cProd"`
	XProd  string `xml:"xProd"`
	NCM    string `xml:"NCM"`
	QCom   string `xml:"qCom"`
	VUnCom string `xml:"vUnCom"`
	VProd  string `xml:"vProd"`
}

func parseFloatOrNil(s string) *float64 {
	s = strings.TrimSpace(s)
	if s == "" {
		return nil
	}
	v, err := strconv.ParseFloat(s, 64)
	if err != nil {
		return nil
	}
	return &v
}

// ParseNFEXML extracts basic invoice and supplier info from an NFe XML document.
func ParseNFEXML(data []byte) (*NFEData, error) {
	var doc nfeXML
	if err := xml.Unmarshal(data, &doc); err != nil {
		return nil, fmt.Errorf("XML inválido: %w", err)
	}

	inf := doc.InfNFe
	if inf.Ide.NNF == "" && inf.Emit.XNome == "" {
		return nil, fmt.Errorf("XML não parece ser uma NF-e válida (infNFe não encontrado)")
	}

	result := &NFEData{
		NumeroNota:       inf.Ide.NNF,
		NaturezaOperacao: inf.Ide.NatOp,
		EmitenteNome:     inf.Emit.XNome,
		EmitenteCNPJ:     inf.Emit.CNPJ,
		EmitenteCidade:   inf.Emit.EnderEmit.XMun,
		EmitenteEstado:   inf.Emit.EnderEmit.UF,
		EmitenteTelefone: inf.Emit.EnderEmit.Fone,
		DestinatarioNome: inf.Dest.XNome,
		DestinatarioCNPJ: inf.Dest.CNPJ,
		Itens:            make([]NFEXMLItem, 0),
	}

	// Endereço do emitente: logradouro, nro, bairro
	endParts := make([]string, 0, 3)
	for _, p := range []string{inf.Emit.EnderEmit.XLgr, inf.Emit.EnderEmit.Nro, inf.Emit.EnderEmit.XBairro} {
		if strings.TrimSpace(p) != "" {
			endParts = append(endParts, strings.TrimSpace(p))
		}
	}
	if len(endParts) > 0 {
		result.EmitenteEndereco = strings.Join(endParts, ", ")
	}

	// Valor total
	result.ValorTotal = parseFloatOrNil(inf.Total.ICMSTot.VNF)

	// Itens
	for _, det := range inf.Dets {
		item := NFEXMLItem{
			Codigo:        det.Prod.CProd,
			Descricao:     det.Prod.XProd,
			NCM:           det.Prod.NCM,
			Quantidade:    parseFloatOrNil(det.Prod.QCom),
			ValorUnitario: parseFloatOrNil(det.Prod.VUnCom),
			ValorTotal:    parseFloatOrNil(det.Prod.VProd),
		}
		result.Itens = append(result.Itens, item)
	}

	// Data de emissão (formato ISO com offset, ex: 2026-08-17T10:00:00-03:00)
	if inf.Ide.DhEmi != "" {
		s := strings.TrimSpace(inf.Ide.DhEmi)
		for _, layout := range []string{time.RFC3339, "2006-01-02T15:04:05"} {
			if t, err := time.Parse(layout, s); err == nil {
				// Python: dt.replace(tzinfo=None) — mantém hora local, sem timezone
				naive := time.Date(t.Year(), t.Month(), t.Day(), t.Hour(), t.Minute(), t.Second(), 0, time.UTC)
				result.DataEmissao = &naive
				break
			}
		}
	}

	return result, nil
}
