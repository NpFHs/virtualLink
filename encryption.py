import rsa

# public_key, private_key = rsa.newkeys(2048)

public_key = rsa.PublicKey(16689707903662139992950132803998776382664643350052287350778398515954785892366368763961259788860586959202466608010713369621567488183245904581288866241030757992319581756724870139006845458914994253388010708656953782151225479851486269271501877307938102990703965907303132073546044096255684078930577796898901633937195247204490759781868285590756634344499859110578731165301457828592237572128163734357867404119583480036101888588881825500854151717269414086739981414930591114539701458520405907558037425517484962948909051781921519459813228196435608748113772268777021521072892041517742064853917712700245117553421250822905803033259, 65537)
private_key = rsa.PrivateKey(16689707903662139992950132803998776382664643350052287350778398515954785892366368763961259788860586959202466608010713369621567488183245904581288866241030757992319581756724870139006845458914994253388010708656953782151225479851486269271501877307938102990703965907303132073546044096255684078930577796898901633937195247204490759781868285590756634344499859110578731165301457828592237572128163734357867404119583480036101888588881825500854151717269414086739981414930591114539701458520405907558037425517484962948909051781921519459813228196435608748113772268777021521072892041517742064853917712700245117553421250822905803033259, 65537, 10505778565660282333173089685157476248385601976945192217663488599984722175315961624554950811444751124020607556752276871849003542388446626296542272119680224761816256859360785399310136298000811342131452366982528515630356225426754574553710704586137273613050664655688899561500656165935761340801277256717462751995334647826728014872654843637763568772791658322899805854642594624091233758800903501744241920264231887560115879840805873285059144772143502283998613525833124689175304782631833584842685445666217614555738647626030688643975157117930634643449710173993256722875165306181500168395533506212760573583908687414244008206913, 2636080374628681556377706732772286162111615273897600310071093532066027846883647501063659550823432296314251372295846925353385565843699785357608177606534035562513617107249942696846810792524948035144563366621853860069309156659117090626689829022154582752804745302462749871664351348538100922934040078935231298801424067435338537579099, 6331259116487695590182374268640287058142807310727949783550151530492874593965739367175662030417544155392161851755189713773629187631065522592247103205365332300149870874423370171512346049570966825555651270130640514440174111488168341921516194234865446565776712723037532550207692742604120889841)


print(f"private_key: {private_key}\npublic_key: {public_key}")


def encrypt(message: str):
    message_split = []
    print(f"len(message): {len(message)}")
    for i in range(0, len(message), 128):
        enc_message = rsa.encrypt(message[i:i + 128].encode(), public_key)
        print(f"enc_message: {enc_message}")
        message_split.append(enc_message)
        print(message_split)
    return "<BREAK>".encode().join(message_split)


def decrypt(enc_message: bytes):
    message = ""
    for i in enc_message.split("<BREAK>".encode()):
        message += rsa.decrypt(i, private_key).decode()
    return message


def set_public_key(key):
    global public_key
    public_key = key


def set_private_key(key):
    global private_key
    private_key = key

e = encrypt("1234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890123456789012345678901234567890")
print(f"e: {e}\n")
print(f"decrypt(e): {decrypt(e)}")


